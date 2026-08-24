"""Chat functions for Cisco Secure Access Connector -- bulk operations and
a combined Umbrella+Meraki health audit (Tier 3 value-add), same shape as
Zscaler Connector's handlers_bulk_audit.py.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import cisco_client as cc
from app import chat
from handlers_connection import _authed_umbrella, _authed_meraki
from schemas import (
    BulkUpdateDestinationListsParams, BulkRebootAppliancesParams,
    BulkActionOutcome, BulkActionResult,
    AuditSecureAccessParams, AuditFinding, AuditReport,
)


@chat.function(
    "bulk_update_destination_lists",
    "Set the same access value (allow/block) on several Umbrella destination lists in one call, by explicit ids. Continues past per-item failures and reports each outcome, same convention as every other bulk_* tool in the portfolio.",
    action_type="write",
)
async def bulk_update_destination_lists(ctx, params: BulkUpdateDestinationListsParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    items: list[BulkActionOutcome] = []
    for dlid in params.destination_list_ids:
        ok, data = await cc.umbrella_request(
            ctx, conn, token, "PATCH", f"/policies/v2/destinationlists/{dlid}",
            json_body={"access": params.access},
        )
        if ok:
            items.append(BulkActionOutcome(id=dlid, ok=True))
        else:
            items.append(BulkActionOutcome(id=dlid, ok=False, error=data.error if hasattr(data, "error") else str(data)))
    return ActionResult(success=True, data=BulkActionResult(title="Bulk destination list access change", items=items))


@chat.function(
    "bulk_reboot_appliances",
    "Reboot several Meraki appliances in one call, by explicit serial numbers. Continues past per-item failures and reports each outcome.",
    action_type="write",
)
async def bulk_reboot_appliances(ctx, params: BulkRebootAppliancesParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    items: list[BulkActionOutcome] = []
    for serial in params.serials:
        ok, data = await cc.meraki_request(ctx, conn, "POST", f"/devices/{serial}/reboot")
        if ok:
            items.append(BulkActionOutcome(id=serial, ok=True))
        else:
            items.append(BulkActionOutcome(id=serial, ok=False, error=data.error if hasattr(data, "error") else str(data)))
    return ActionResult(success=True, data=BulkActionResult(title="Bulk appliance reboot", items=items))


@chat.function(
    "audit_secure_access",
    "Build one aggregated health report across the connected Cisco Umbrella/Secure Access and Meraki organization: unassigned destination lists, offline roaming computers, offline appliances, and recent alert volume -- the same 'audit_*' value-add pattern as every other connector in the portfolio.",
    action_type="write",
)
async def audit_secure_access(ctx, params: AuditSecureAccessParams) -> ActionResult:
    findings: list[AuditFinding] = []
    unassigned_dl = 0
    offline_rc = 0
    offline_appl = 0
    recent_alerts = 0

    auth_u = await _authed_umbrella(ctx, params.umbrella_connection_id)
    if not isinstance(auth_u, ActionResult):
        conn, token = auth_u
        ok, data = await cc.umbrella_request(ctx, conn, token, "GET", "/policies/v2/destinationlists")
        if ok:
            dls = data if isinstance(data, list) else data.get("data", [])
            unassigned_dl = sum(1 for d in dls if not d.get("isGlobal") and d.get("meta", {}).get("total", 0) == 0)
            findings.append(AuditFinding(
                id="empty_destination_lists", title="Empty destination lists",
                severity="low" if unassigned_dl == 0 else "medium",
                detail=f"{unassigned_dl} destination list(s) have no entries yet.",
            ))
        ok, data = await cc.umbrella_request(ctx, conn, token, "GET", "/deployments/v2/roamingcomputers")
        if ok:
            rcs = data if isinstance(data, list) else data.get("data", [])
            offline_rc = sum(1 for rc in rcs if rc.get("status") != "active")
            findings.append(AuditFinding(
                id="offline_roaming_computers", title="Offline roaming computers",
                severity="info" if offline_rc == 0 else "medium",
                detail=f"{offline_rc} of {len(rcs)} roaming computer(s) are not active.",
            ))

    auth_m = await _authed_meraki(ctx, params.meraki_connection_id)
    if not isinstance(auth_m, ActionResult):
        conn, _ = auth_m
        org_id = conn.get("organization_id", "")
        ok, data = await cc.meraki_request(ctx, conn, "GET", f"/organizations/{org_id}/appliance/uplink/statuses")
        if ok:
            appliances = data if isinstance(data, list) else []
            offline_appl = sum(
                1 for a in appliances
                if any(u.get("status") not in ("active", "ready") for u in a.get("uplinks", []))
            )
            findings.append(AuditFinding(
                id="offline_appliances", title="Appliances with a down/degraded uplink",
                severity="info" if offline_appl == 0 else "high",
                detail=f"{offline_appl} of {len(appliances)} appliance(s) have an uplink issue.",
            ))
        ok, data = await cc.meraki_request(ctx, conn, "GET", f"/organizations/{org_id}/assurance/alerts")
        if ok:
            alerts = data if isinstance(data, list) else data.get("items", [])
            recent_alerts = len(alerts)
            findings.append(AuditFinding(
                id="recent_alerts", title="Recent alerts",
                severity="info" if recent_alerts == 0 else "medium",
                detail=f"{recent_alerts} alert(s) currently open.",
            ))

    return ActionResult(success=True, data=AuditReport(
        title="Cisco Secure Access health audit",
        unassigned_destination_lists=unassigned_dl,
        offline_roaming_computers=offline_rc,
        offline_appliances=offline_appl,
        recent_alerts_24h=recent_alerts,
        findings=findings,
    ))
