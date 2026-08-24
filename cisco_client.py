"""Cisco Umbrella / Secure Access + Meraki HTTP clients -- two independent
BYOK auth mechanisms under one connector, same shape as Zscaler Connector's
zscaler_client.py.

WHY `ctx.http.*`, NOT A RAW `httpx` CLIENT -- same convention as every other
connector in this portfolio: the SDK's own async HTTP client goes through
the platform's sandboxed egress path.

Umbrella / Secure Access: OAuth2 client_credentials against
`https://api.umbrella.com/auth/v2/token` using HTTP Basic auth with
api_key:api_secret, then Bearer token against `https://api.umbrella.com/...`.

Meraki: static `X-Cisco-Meraki-API-Key` header against
`https://api.meraki.com/api/v1/...` -- no token exchange at all.
"""
from __future__ import annotations

import base64
from typing import Any

UMBRELLA_TOKEN_URL = "https://api.umbrella.com/auth/v2/token"
UMBRELLA_API_BASE = "https://api.umbrella.com"
MERAKI_API_BASE = "https://api.meraki.com/api/v1"

ACCOUNT_MISSING = "CISCO_ACCOUNT_MISSING"
TOKEN_REJECTED = "CISCO_TOKEN_REJECTED"
PERMISSION_DENIED = "CISCO_PERMISSION_DENIED"
NOT_FOUND = "CISCO_NOT_FOUND"
VALIDATION_FAILED = "CISCO_VALIDATION_FAILED"
RESPONSE_UNEXPECTED = "CISCO_RESPONSE_UNEXPECTED"
UNREACHABLE = "CISCO_UNREACHABLE"
RATE_LIMITED = "CISCO_RATE_LIMITED"
BACKEND_5XX = "CISCO_BACKEND_5XX"
BACKEND_TIMEOUT = "CISCO_BACKEND_TIMEOUT"

_MESSAGES = {
    ACCOUNT_MISSING: "No Cisco Umbrella/Meraki connection is set up yet.",
    TOKEN_REJECTED: "Cisco rejected these credentials. Check the API key/secret, then reconnect.",
    PERMISSION_DENIED: "Cisco accepted the credentials, but this key lacks the required scope for this operation.",
    NOT_FOUND: "Cisco has no such resource, or this account cannot access it.",
    VALIDATION_FAILED: "Cisco rejected the request as invalid.",
    RESPONSE_UNEXPECTED: "Cisco returned a response the connector could not safely interpret.",
    UNREACHABLE: "Could not reach Cisco.",
    RATE_LIMITED: "Cisco is rate-limiting requests; try again shortly.",
    BACKEND_5XX: "Cisco returned a server error; try again shortly.",
    BACKEND_TIMEOUT: "Cisco took too long to respond; try again shortly.",
}
_RETRYABLE = {RATE_LIMITED, BACKEND_5XX, BACKEND_TIMEOUT}


def fail(code: str, detail: str = "") -> dict:
    message = _MESSAGES.get(code, code)
    if detail:
        message = f"{message} ({detail})"
    return {"ok": False, "error_code": code, "error": message, "retryable": code in _RETRYABLE}


class ClientFail(Exception):
    def __init__(self, payload: dict):
        super().__init__(payload.get("error", "Cisco request failed"))
        self.payload = payload


def _check(resp) -> Any:
    status = getattr(resp, "status_code", 0)
    if status == 401:
        raise ClientFail(fail(TOKEN_REJECTED))
    if status == 403:
        raise ClientFail(fail(PERMISSION_DENIED))
    if status == 404:
        raise ClientFail(fail(NOT_FOUND))
    if status == 429:
        raise ClientFail(fail(RATE_LIMITED))
    if status >= 500:
        raise ClientFail(fail(BACKEND_5XX, f"HTTP {status}"))
    if status >= 400:
        raise ClientFail(fail(VALIDATION_FAILED, f"HTTP {status}"))
    if status == 204:
        return {}
    body = getattr(resp, "body", None)
    if body is not None:
        return body
    try:
        return resp.json()
    except Exception:
        raise ClientFail(fail(RESPONSE_UNEXPECTED))


# ──────────────────────────────────────────────────────────────────────────
# Umbrella / Secure Access
# ──────────────────────────────────────────────────────────────────────────


async def get_umbrella_token(ctx, api_key: str, api_secret: str) -> dict:
    if not api_key or not api_secret:
        return fail(ACCOUNT_MISSING)
    basic = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
    try:
        resp = await ctx.http.post(
            UMBRELLA_TOKEN_URL,
            data={"grant_type": "client_credentials"},
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    except Exception as exc:
        return fail(UNREACHABLE, str(exc))
    status = getattr(resp, "status_code", 0)
    if status == 401:
        return fail(TOKEN_REJECTED)
    if status >= 500:
        return fail(BACKEND_5XX, f"HTTP {status}")
    if status == 429:
        return fail(RATE_LIMITED)
    if status >= 400:
        return fail(VALIDATION_FAILED, f"HTTP {status}")
    body = resp.body if isinstance(getattr(resp, "body", None), dict) else {}
    if not body:
        try:
            body = resp.json()
        except Exception:
            body = {}
    token = body.get("access_token")
    if not token:
        return fail(RESPONSE_UNEXPECTED, "no access_token in response")
    return {"ok": True, "access_token": token, "expires_in": int(body.get("expires_in", 3600))}


async def umbrella_request(ctx, access_token: str, method: str, path: str,
                            params: dict | None = None, json_body: dict | None = None) -> Any:
    url = f"{UMBRELLA_API_BASE}{path}"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    method = method.upper()
    try:
        if method == "GET":
            resp = await ctx.http.get(url, headers=headers, params=params or {})
        elif method == "POST":
            resp = await ctx.http.post(url, headers=headers, json=json_body or {})
        elif method == "PUT":
            resp = await ctx.http.put(url, headers=headers, json=json_body or {})
        elif method == "PATCH":
            resp = await ctx.http.request("PATCH", url, headers=headers, json=json_body or {})
        elif method == "DELETE":
            resp = await ctx.http.delete(url, headers=headers)
        else:
            resp = await ctx.http.request(method, url, headers=headers, json=json_body or {}, params=params or {})
    except ClientFail:
        raise
    except Exception as exc:
        raise ClientFail(fail(UNREACHABLE, str(exc)))
    return _check(resp)


# ──────────────────────────────────────────────────────────────────────────
# Meraki -- static API key header, no token exchange
# ──────────────────────────────────────────────────────────────────────────


async def meraki_request(ctx, api_key: str, method: str, path: str,
                          params: dict | None = None, json_body: dict | None = None) -> Any:
    if not api_key:
        raise ClientFail(fail(ACCOUNT_MISSING))
    url = f"{MERAKI_API_BASE}{path}"
    headers = {"X-Cisco-Meraki-API-Key": api_key, "Content-Type": "application/json"}
    method = method.upper()
    try:
        if method == "GET":
            resp = await ctx.http.get(url, headers=headers, params=params or {})
        elif method == "POST":
            resp = await ctx.http.post(url, headers=headers, json=json_body or {})
        elif method == "PUT":
            resp = await ctx.http.put(url, headers=headers, json=json_body or {})
        elif method == "DELETE":
            resp = await ctx.http.delete(url, headers=headers)
        else:
            resp = await ctx.http.request(method, url, headers=headers, json=json_body or {}, params=params or {})
    except ClientFail:
        raise
    except Exception as exc:
        raise ClientFail(fail(UNREACHABLE, str(exc)))
    return _check(resp)


async def meraki_verify(ctx, api_key: str) -> dict:
    """Verify a Meraki API key actually works by listing organizations."""
    try:
        orgs = await meraki_request(ctx, api_key, "GET", "/organizations")
    except ClientFail as exc:
        return exc.payload
    if not isinstance(orgs, list):
        return fail(RESPONSE_UNEXPECTED)
    return {"ok": True, "organizations": orgs}
