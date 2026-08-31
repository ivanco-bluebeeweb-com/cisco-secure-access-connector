"""Chat functions for Cisco Secure Access Connector: connection management
(Umbrella/Secure Access + Meraki, two independent BYOK auth mechanisms).
Built on cisco_client.py / schemas.py, following the same shape as Zscaler
Connector's handlers_connection.py.
"""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import cisco_client as cc
from app import ext, chat
from schemas import (
    NoParams,
    ConnectUmbrellaParams, ConnectMerakiParams,
    ProviderConnection, ProviderConnectionList,
    DisconnectParams, DeleteResult,
)

_SECRET_NAME = "cisco_secure_access_connections"


# ──────────────────────────────────────────────────────────────────────────
# Connection storage helpers -- one secret holding a JSON array of BOTH
# umbrella and meraki connections (kind="umbrella"|"meraki"), same
# precedent as Zscaler Connector / MuleSoft Connector.
# ──────────────────────────────────────────────────────────────────────────


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


async def _resolve_connection(ctx, kind: str, connection_id: str = "") -> dict | None:
    connections = [c for c in await _load_connections(ctx) if c.get("kind") == kind]
    if not connections:
        return None
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        return None
    return connections[0]


def _connection_to_entity(c: dict) -> ProviderConnection:
    kind = c.get("kind", "")
    if kind == "umbrella":
        detail = "Umbrella / Secure Access"
    elif kind == "meraki":
        org = c.get("organization_id", "")
        detail = f"Meraki -- org {org}" if org else "Meraki"
    else:
        detail = kind
    return ProviderConnection(
        id=c.get("id", ""), title=c.get("label") or detail, kind=kind,
        connected=True, detail=detail,
    )


async def _authed_umbrella(ctx, connection_id: str = "") -> tuple[dict, str] | ActionResult:
    conn = await _resolve_connection(ctx, "umbrella", connection_id)
    if not conn:
        return ActionResult.fail(cc.ACCOUNT_MISSING, "No Umbrella/Secure Access connection is set up yet.")
    tok = await cc.get_umbrella_token(ctx, conn.get("api_key", ""), conn.get("api_secret", ""))
    if not tok.get("ok"):
        return ActionResult.fail(tok["error_code"], tok["error"])
    return conn, tok["access_token"]


async def _authed_meraki(ctx, connection_id: str = "") -> tuple[dict, str] | ActionResult:
    conn = await _resolve_connection(ctx, "meraki", connection_id)
    if not conn:
        return ActionResult.fail(cc.ACCOUNT_MISSING, "No Meraki connection is set up yet.")
    return conn, conn.get("meraki_api_key", "")


# ──────────────────────────────────────────────────────────────────────────
# Connection management
# ──────────────────────────────────────────────────────────────────────────


@chat.function(
    "connect_umbrella",
    "Connect your Cisco Umbrella/Secure Access account by saving its API key and secret, after checking they actually work. Create one in Umbrella dashboard > Admin > API Keys.",
    action_type="write",
)
async def connect_umbrella(ctx, params: ConnectUmbrellaParams) -> ActionResult:
    """Connect your Cisco Umbrella/Secure Access account by saving its API
    key and secret, after checking they actually work. Create one in
    Umbrella dashboard > Admin > API Keys."""
    if not params.api_key or not params.api_secret:
        return ActionResult.fail(cc.VALIDATION_FAILED, "api_key and api_secret are both required.")
    tok = await cc.get_umbrella_token(ctx, params.api_key, params.api_secret)
    if not tok.get("ok"):
        return ActionResult.fail(tok["error_code"], tok["error"])
    connections = await _load_connections(ctx)
    conn_id = str(uuid.uuid4())
    connections.append({
        "id": conn_id, "kind": "umbrella",
        "api_key": params.api_key, "api_secret": params.api_secret,
        "label": params.label,
    })
    await _save_connections(ctx, connections)
    return ActionResult.success(ProviderConnection(
        id=conn_id, title=params.label or "Umbrella / Secure Access", kind="umbrella",
        connected=True, detail="Umbrella / Secure Access",
    ), summary="Umbrella connected.")


@chat.function(
    "connect_meraki",
    "Connect your Cisco Meraki organization by saving its Dashboard API key, after checking it actually works. Create one in Meraki Dashboard > My profile > API access.",
    action_type="write",
)
async def connect_meraki(ctx, params: ConnectMerakiParams) -> ActionResult:
    """Connect your Cisco Meraki organization by saving its Dashboard API
    key, after checking it actually works. Create one in Meraki Dashboard
    > My profile > API access."""
    if not params.meraki_api_key:
        return ActionResult.fail(cc.VALIDATION_FAILED, "meraki_api_key is required.")
    verify = await cc.meraki_verify(ctx, params.meraki_api_key)
    if not verify.get("ok"):
        return ActionResult.fail(verify["error_code"], verify["error"])
    org_id = params.organization_id
    if not org_id:
        orgs = verify.get("organizations") or []
        if orgs:
            org_id = orgs[0].get("id", "")
    connections = await _load_connections(ctx)
    conn_id = str(uuid.uuid4())
    connections.append({
        "id": conn_id, "kind": "meraki",
        "meraki_api_key": params.meraki_api_key, "organization_id": org_id,
        "label": params.label,
    })
    await _save_connections(ctx, connections)
    return ActionResult.success(ProviderConnection(
        id=conn_id, title=params.label or f"Meraki -- org {org_id}", kind="meraki",
        connected=True, detail=f"Meraki -- org {org_id}" if org_id else "Meraki",
    ), summary="Meraki connected.")


@chat.function(
    "disconnect_cisco",
    "Disconnect a Cisco Umbrella/Secure Access or Meraki connection: deletes the saved credentials. Nothing in Cisco itself is changed.",
    action_type="write",
)
async def disconnect_cisco(ctx, params: DisconnectParams) -> ActionResult:
    """Disconnect a Cisco Umbrella/Secure Access or Meraki connection:
    deletes the saved credentials. Nothing in Cisco itself is changed."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.fail(cc.NOT_FOUND, "No such connection.")
    await _save_connections(ctx, remaining)
    return ActionResult.success(DeleteResult(id=params.connection_id, ok=True), summary="Cisco disconnected.")


@chat.function(
    "list_connections",
    "List the connected Cisco Umbrella/Secure Access and Meraki accounts.",
    action_type="read",
    data_model=ProviderConnectionList,
)
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """List the connected Cisco Umbrella/Secure Access and Meraki accounts."""
    connections = await _load_connections(ctx)
    return ActionResult.success(ProviderConnectionList(items=[_connection_to_entity(c) for c in connections]), summary="Connections listed.")
