"""Chat functions for Meraki (SD-WAN side of Cisco Secure Access): organizations,
networks, uplink status, VPN topology, appliance health, and alerts. Built on
cisco_client.py / schemas.py, following the same shape as handlers_umbrella.py.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import cisco_client as cc
from app import chat
from handlers_connection import _authed_meraki
from schemas import (
    ListMerakiOrganizationsParams, MerakiOrganization, MerakiOrganizationList,
    ListMerakiNetworksParams, MerakiNetwork, MerakiNetworkList,
    GetMerakiNetworkParams, CreateMerakiNetworkParams, UpdateMerakiNetworkParams,
    DeleteMerakiNetworkParams, DeleteResult,
    ListUplinkStatusesParams, UplinkStatus, UplinkStatusList,
    ListVpnTopologyParams, VpnPeer, VpnTopologyResult,
    ListApplianceHealthParams, ApplianceHealth, ApplianceHealthList,
    RebootApplianceParams, RebootResult,
    ListAlertsParams, Alert, AlertList,
    CreateAlertWebhookParams, WebhookResult,
)


@chat.function(
    "list_meraki_organizations",
    "List Meraki organizations visible to the connected API key.",
    action_type="read",
    data_model=MerakiOrganizationList,
)
async def list_meraki_organizations(ctx, params: ListMerakiOrganizationsParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    ok, data = await cc.meraki_request(ctx, conn, "GET", "/organizations")
    if not ok:
        return data
    items = [MerakiOrganization(id=str(o.get("id", "")), title=o.get("name", ""), url=o.get("url", "")) for o in data]
    return ActionResult(success=True, data=MerakiOrganizationList(title=f"{len(items)} organization(s)", items=items))


@chat.function(
    "list_meraki_networks",
    "List networks in the connected Meraki organization.",
    action_type="read",
    data_model=MerakiNetworkList,
)
async def list_meraki_networks(ctx, params: ListMerakiNetworksParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    org_id = conn.get("organization_id", "")
    ok, data = await cc.meraki_request(ctx, conn, "GET", f"/organizations/{org_id}/networks")
    if not ok:
        return data
    items = [
        MerakiNetwork(id=n.get("id", ""), title=n.get("name", ""),
                       product_types=n.get("productTypes", []), time_zone=n.get("timeZone", ""))
        for n in data
    ]
    return ActionResult(success=True, data=MerakiNetworkList(title=f"{len(items)} network(s)", items=items))


@chat.function(
    "get_meraki_network",
    "Read one Meraki network in full.",
    action_type="read",
    data_model=MerakiNetwork,
)
async def get_meraki_network(ctx, params: GetMerakiNetworkParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    ok, data = await cc.meraki_request(ctx, conn, "GET", f"/networks/{params.network_id}")
    if not ok:
        return data
    return ActionResult(success=True, data=MerakiNetwork(
        id=data.get("id", ""), title=data.get("name", ""),
        product_types=data.get("productTypes", []), time_zone=data.get("timeZone", ""),
    ))


@chat.function(
    "create_meraki_network",
    "Create a new network in the connected Meraki organization.",
    action_type="write",
    data_model=MerakiNetwork,
)
async def create_meraki_network(ctx, params: CreateMerakiNetworkParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    org_id = conn.get("organization_id", "")
    body = {"name": params.name, "productTypes": params.product_types or ["appliance"]}
    if params.time_zone:
        body["timeZone"] = params.time_zone
    ok, data = await cc.meraki_request(ctx, conn, "POST", f"/organizations/{org_id}/networks", json_body=body)
    if not ok:
        return data
    return ActionResult(success=True, data=MerakiNetwork(
        id=data.get("id", ""), title=data.get("name", ""),
        product_types=data.get("productTypes", []), time_zone=data.get("timeZone", ""),
    ))


@chat.function(
    "update_meraki_network",
    "Update selected fields of an existing Meraki network. Only given fields change.",
    action_type="write",
    data_model=MerakiNetwork,
)
async def update_meraki_network(ctx, params: UpdateMerakiNetworkParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    body = {}
    if params.name:
        body["name"] = params.name
    ok, data = await cc.meraki_request(ctx, conn, "PUT", f"/networks/{params.network_id}", json_body=body)
    if not ok:
        return data
    return ActionResult(success=True, data=MerakiNetwork(
        id=data.get("id", ""), title=data.get("name", ""),
        product_types=data.get("productTypes", []), time_zone=data.get("timeZone", ""),
    ))


@chat.function(
    "delete_meraki_network",
    "Permanently delete a Meraki network. Cannot be undone.",
    action_type="write",
    data_model=DeleteResult,
)
async def delete_meraki_network(ctx, params: DeleteMerakiNetworkParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    ok, data = await cc.meraki_request(ctx, conn, "DELETE", f"/networks/{params.network_id}")
    if not ok:
        return data
    return ActionResult(success=True, data=DeleteResult(id=params.network_id, title="Network deleted", ok=True))


@chat.function(
    "list_uplink_statuses",
    "List SD-WAN uplink statuses for appliances in the connected Meraki organization.",
    action_type="read",
    data_model=UplinkStatusList,
)
async def list_uplink_statuses(ctx, params: ListUplinkStatusesParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    org_id = conn.get("organization_id", "")
    ok, data = await cc.meraki_request(ctx, conn, "GET", f"/organizations/{org_id}/appliance/uplink/statuses")
    if not ok:
        return data
    items: list[UplinkStatus] = []
    for dev in data:
        for uplink in dev.get("uplinks", []):
            items.append(UplinkStatus(
                id=f"{dev.get('networkId', '')}:{uplink.get('interface', '')}",
                title=dev.get("networkId", ""), network_id=dev.get("networkId", ""),
                interface=uplink.get("interface", ""), status=uplink.get("status", ""),
                ip=uplink.get("ip", ""),
            ))
    return ActionResult(success=True, data=UplinkStatusList(title=f"{len(items)} uplink(s)", items=items))


@chat.function(
    "list_vpn_topology",
    "List Meraki VPN (AutoVPN) topology -- peer status between networks.",
    action_type="read",
    data_model=VpnTopologyResult,
)
async def list_vpn_topology(ctx, params: ListVpnTopologyParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    org_id = conn.get("organization_id", "")
    ok, data = await cc.meraki_request(ctx, conn, "GET", f"/organizations/{org_id}/appliance/vpn/statuses")
    if not ok:
        return data
    items: list[VpnPeer] = []
    for entry in data:
        for peer in entry.get("merakiVpnPeers", []):
            items.append(VpnPeer(
                id=f"{entry.get('networkId', '')}:{peer.get('networkName', '')}",
                title=peer.get("networkName", ""), network_a=entry.get("networkName", ""),
                network_b=peer.get("networkName", ""), status=peer.get("reachability", ""),
            ))
    return ActionResult(success=True, data=VpnTopologyResult(title=f"{len(items)} VPN peer(s)", items=items))


@chat.function(
    "list_appliance_health",
    "List Meraki MX appliance health/connectivity status across the connected organization.",
    action_type="read",
    data_model=ApplianceHealthList,
)
async def list_appliance_health(ctx, params: ListApplianceHealthParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    org_id = conn.get("organization_id", "")
    ok, data = await cc.meraki_request(ctx, conn, "GET", f"/organizations/{org_id}/devices/statuses")
    if not ok:
        return data
    items = [
        ApplianceHealth(
            id=d.get("serial", ""), title=d.get("name") or d.get("serial", ""),
            serial=d.get("serial", ""), model=d.get("model", ""),
            status=d.get("status", ""), network_id=d.get("networkId", ""),
        )
        for d in data if "MX" in (d.get("model", "") or "")
    ]
    return ActionResult(success=True, data=ApplianceHealthList(title=f"{len(items)} appliance(s)", items=items))


@chat.function(
    "reboot_appliance",
    "Reboot a Meraki MX appliance by serial number.",
    action_type="write",
    data_model=RebootResult,
)
async def reboot_appliance(ctx, params: RebootApplianceParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    ok, data = await cc.meraki_request(ctx, conn, "POST", f"/devices/{params.serial}/reboot")
    if not ok:
        return data
    return ActionResult(success=True, data=RebootResult(id=params.serial, title="Reboot requested", ok=True))


@chat.function(
    "list_alerts",
    "List Meraki alerts across the organization, optionally filtered to one network.",
    action_type="read",
    data_model=AlertList,
)
async def list_alerts(ctx, params: ListAlertsParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    org_id = conn.get("organization_id", "")
    query = {"networkId": params.network_id} if params.network_id else None
    ok, data = await cc.meraki_request(ctx, conn, "GET", f"/organizations/{org_id}/assurance/alerts", query=query)
    if not ok:
        return data
    items = [
        Alert(
            id=a.get("id", ""), title=a.get("title", a.get("type", "")),
            category=a.get("category", ""), severity=a.get("severity", ""),
            occurred_at=str(a.get("startedAt", "")),
        )
        for a in (data if isinstance(data, list) else data.get("items", []))
    ]
    return ActionResult(success=True, data=AlertList(title=f"{len(items)} alert(s)", items=items))


@chat.function(
    "create_alert_webhook",
    "Create a webhook receiver on a Meraki network so alerts push to an HTTPS URL.",
    action_type="write",
    data_model=WebhookResult,
)
async def create_alert_webhook(ctx, params: CreateAlertWebhookParams) -> ActionResult:
    auth = await _authed_meraki(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, _ = auth
    body = {"name": params.name, "url": params.url}
    ok, data = await cc.meraki_request(ctx, conn, "POST", f"/networks/{params.network_id}/webhooks/httpServers", json_body=body)
    if not ok:
        return data
    return ActionResult(success=True, data=WebhookResult(id=data.get("id", ""), title=data.get("name", ""), url=data.get("url", "")))
