"""Pydantic params models + SDL entity contracts for Cisco Secure Access Connector.

All params models are module-scope (V17 federal invariant, same rule as
Zscaler Connector's / MuleSoft Connector's schemas.py).
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from imperal_sdk import sdl


class NoParams(BaseModel):
    """Explicit empty params model -- V17 disallows untyped handlers."""
    pass


# ──────────────────────────────────────────────────────────────────────────
# Connection
# ──────────────────────────────────────────────────────────────────────────


class ConnectUmbrellaParams(BaseModel):
    api_key: str = Field("", description="Umbrella/Secure Access API key (Admin > API Keys > Umbrella Management/Reporting).")
    api_secret: str = Field("", description="Umbrella/Secure Access API secret.")
    label: str = Field("", description="Optional friendly name for this Umbrella connection.")


class ConnectMerakiParams(BaseModel):
    meraki_api_key: str = Field("", description="Meraki Dashboard API key (My profile > API access).")
    organization_id: str = Field("", description="Optional Meraki organization id. Empty = auto-resolve the first visible organization.")
    label: str = Field("", description="Optional friendly name for this Meraki connection.")


class ProviderConnection(sdl.Entity):
    id: str = ""
    title: str = ""
    kind: str = ""  # "umbrella" | "meraki"
    connected: bool = False
    detail: str = ""


class ProviderConnectionList(sdl.Entity):
    id: str = "provider_connection_list"
    title: str = ""
    items: list[ProviderConnection] = Field(default_factory=list)


class DisconnectParams(BaseModel):
    connection_id: str = Field(..., description="Connection id to disconnect, from list_connections.")


class DeleteResult(sdl.Entity):
    id: str = ""
    title: str = ""
    ok: bool = True


class _UmbrellaScoped(BaseModel):
    connection_id: str = Field("", description="Which connected Umbrella/Secure Access org to use. Omit if only one is connected.")


class _MerakiScoped(BaseModel):
    connection_id: str = Field("", description="Which connected Meraki organization to use. Omit if only one is connected.")


# ──────────────────────────────────────────────────────────────────────────
# Umbrella -- Destination Lists
# ──────────────────────────────────────────────────────────────────────────


class ListDestinationListsParams(_UmbrellaScoped):
    search: str = Field("", description="Optional name substring filter.")


class DestinationList(sdl.Entity):
    id: str = ""
    title: str = ""
    access: str = ""  # "allow" | "block"
    entry_count: int = 0
    is_global: bool = False


class DestinationListList(sdl.Entity):
    id: str = "destination_list_list"
    title: str = ""
    items: list[DestinationList] = Field(default_factory=list)


class GetDestinationListParams(_UmbrellaScoped):
    destination_list_id: str = Field(..., description="Destination list id, from list_destination_lists.")


class CreateDestinationListParams(_UmbrellaScoped):
    name: str = Field(..., description="Destination list name, e.g. 'Blocked malware domains'.")
    access: str = Field("block", description="allow or block.")


class UpdateDestinationListParams(_UmbrellaScoped):
    destination_list_id: str = Field(..., description="Destination list id to update.")
    name: str = Field("", description="New name, if changing.")


class DeleteDestinationListParams(_UmbrellaScoped):
    destination_list_id: str = Field(..., description="Destination list id to permanently delete.")


class AddDestinationListEntryParams(_UmbrellaScoped):
    destination_list_id: str = Field(..., description="Destination list id to add entries to.")
    destinations: list[str] = Field(..., description="Domains/URLs/IPs to add to the list.")


class RemoveDestinationListEntryParams(_UmbrellaScoped):
    destination_list_id: str = Field(..., description="Destination list id to remove entries from.")
    destinations: list[str] = Field(..., description="Domains/URLs/IPs to remove from the list.")


# ──────────────────────────────────────────────────────────────────────────
# Umbrella -- Policies
# ──────────────────────────────────────────────────────────────────────────


class ListPoliciesParams(_UmbrellaScoped):
    pass


class Policy(sdl.Entity):
    id: str = ""
    title: str = ""
    priority: int = 0
    identity_count: int = 0


class PolicyList(sdl.Entity):
    id: str = "policy_list"
    title: str = ""
    items: list[Policy] = Field(default_factory=list)


class GetPolicyParams(_UmbrellaScoped):
    policy_id: str = Field(..., description="Policy id, from list_policies.")


# ──────────────────────────────────────────────────────────────────────────
# Umbrella -- Identities (Networks, Roaming Computers, Virtual Appliances)
# ──────────────────────────────────────────────────────────────────────────


class ListNetworksParams(_UmbrellaScoped):
    pass


class UmbrellaNetwork(sdl.Entity):
    id: str = ""
    title: str = ""
    ip_address: str = ""
    status: str = ""


class UmbrellaNetworkList(sdl.Entity):
    id: str = "umbrella_network_list"
    title: str = ""
    items: list[UmbrellaNetwork] = Field(default_factory=list)


class ListRoamingComputersParams(_UmbrellaScoped):
    search: str = Field("", description="Optional hostname/user substring filter.")


class RoamingComputer(sdl.Entity):
    id: str = ""
    title: str = ""
    os_version: str = ""
    status: str = ""  # "active" | "inactive"
    last_sync: str = ""


class RoamingComputerList(sdl.Entity):
    id: str = "roaming_computer_list"
    title: str = ""
    items: list[RoamingComputer] = Field(default_factory=list)


class ListVirtualAppliancesParams(_UmbrellaScoped):
    pass


class VirtualAppliance(sdl.Entity):
    id: str = ""
    title: str = ""
    status: str = ""


class VirtualApplianceList(sdl.Entity):
    id: str = "virtual_appliance_list"
    title: str = ""
    items: list[VirtualAppliance] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────
# Umbrella -- ZTNA Private Resources
# ──────────────────────────────────────────────────────────────────────────


class ListPrivateResourcesParams(_UmbrellaScoped):
    pass


class PrivateResource(sdl.Entity):
    id: str = ""
    title: str = ""
    address: str = ""
    protocol: str = ""
    policy_name: str = ""


class PrivateResourceList(sdl.Entity):
    id: str = "private_resource_list"
    title: str = ""
    items: list[PrivateResource] = Field(default_factory=list)


class GetPrivateResourceParams(_UmbrellaScoped):
    resource_id: str = Field(..., description="Private resource id, from list_private_resources.")


class CreatePrivateResourceParams(_UmbrellaScoped):
    name: str = Field(..., description="Private resource name.")
    address: str = Field(..., description="Hostname/IP of the private application.")
    protocol: str = Field("tcp", description="tcp or udp.")
    ports: list[str] = Field(default_factory=list, description="Port(s)/ranges, e.g. ['443','8080-8090'].")


class UpdatePrivateResourceParams(_UmbrellaScoped):
    resource_id: str = Field(..., description="Private resource id to update.")
    name: str = Field("", description="New name, if changing.")


class DeletePrivateResourceParams(_UmbrellaScoped):
    resource_id: str = Field(..., description="Private resource id to permanently delete.")


# ──────────────────────────────────────────────────────────────────────────
# Umbrella -- Reporting
# ──────────────────────────────────────────────────────────────────────────


class ListActivityParams(_UmbrellaScoped):
    limit: int = Field(50, description="Max rows to return.")


class ActivityEntry(sdl.Entity):
    id: str = ""
    title: str = ""
    timestamp: str = ""
    identity: str = ""
    destination: str = ""
    action: str = ""  # "allowed" | "blocked"
    categories: list[str] = Field(default_factory=list)


class ActivityList(sdl.Entity):
    id: str = "activity_list"
    title: str = ""
    items: list[ActivityEntry] = Field(default_factory=list)


class GetTopReportParams(_UmbrellaScoped):
    report: str = Field("destinations", description="One of: destinations, categories, identities.")
    limit: int = Field(10, description="Max rows to return.")


class TopReportRow(sdl.Entity):
    id: str = ""
    title: str = ""
    count: int = 0


class TopReportResult(sdl.Entity):
    id: str = "top_report_result"
    title: str = ""
    items: list[TopReportRow] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────
# Meraki -- Organizations / Networks
# ──────────────────────────────────────────────────────────────────────────


class ListMerakiOrganizationsParams(_MerakiScoped):
    pass


class MerakiOrganization(sdl.Entity):
    id: str = ""
    title: str = ""
    url: str = ""


class MerakiOrganizationList(sdl.Entity):
    id: str = "meraki_organization_list"
    title: str = ""
    items: list[MerakiOrganization] = Field(default_factory=list)


class ListMerakiNetworksParams(_MerakiScoped):
    pass


class MerakiNetwork(sdl.Entity):
    id: str = ""
    title: str = ""
    product_types: list[str] = Field(default_factory=list)
    time_zone: str = ""


class MerakiNetworkList(sdl.Entity):
    id: str = "meraki_network_list"
    title: str = ""
    items: list[MerakiNetwork] = Field(default_factory=list)


class GetMerakiNetworkParams(_MerakiScoped):
    network_id: str = Field(..., description="Meraki network id, from list_meraki_networks.")


class CreateMerakiNetworkParams(_MerakiScoped):
    name: str = Field(..., description="Network name.")
    product_types: list[str] = Field(default_factory=list, description="e.g. ['appliance','switch','wireless'].")
    time_zone: str = Field("", description="e.g. 'Europe/Chisinau'.")


class UpdateMerakiNetworkParams(_MerakiScoped):
    network_id: str = Field(..., description="Network id to update.")
    name: str = Field("", description="New name, if changing.")


class DeleteMerakiNetworkParams(_MerakiScoped):
    network_id: str = Field(..., description="Network id to permanently delete.")


# ──────────────────────────────────────────────────────────────────────────
# Meraki -- SD-WAN / Appliance / VPN
# ──────────────────────────────────────────────────────────────────────────


class ListUplinkStatusesParams(_MerakiScoped):
    pass


class UplinkStatus(sdl.Entity):
    id: str = ""
    title: str = ""
    network_id: str = ""
    interface: str = ""
    status: str = ""  # "active" | "ready" | "failed" | "not connected"
    ip: str = ""


class UplinkStatusList(sdl.Entity):
    id: str = "uplink_status_list"
    title: str = ""
    items: list[UplinkStatus] = Field(default_factory=list)


class ListVpnTopologyParams(_MerakiScoped):
    pass


class VpnPeer(sdl.Entity):
    id: str = ""
    title: str = ""
    network_a: str = ""
    network_b: str = ""
    status: str = ""


class VpnTopologyResult(sdl.Entity):
    id: str = "vpn_topology_result"
    title: str = ""
    items: list[VpnPeer] = Field(default_factory=list)


class ListApplianceHealthParams(_MerakiScoped):
    pass


class ApplianceHealth(sdl.Entity):
    id: str = ""
    title: str = ""
    serial: str = ""
    model: str = ""
    status: str = ""  # "online" | "offline" | "alerting"
    network_id: str = ""


class ApplianceHealthList(sdl.Entity):
    id: str = "appliance_health_list"
    title: str = ""
    items: list[ApplianceHealth] = Field(default_factory=list)


class RebootApplianceParams(_MerakiScoped):
    serial: str = Field(..., description="Serial number of the appliance to reboot.")


class RebootResult(sdl.Entity):
    id: str = ""
    title: str = ""
    ok: bool = True


# ──────────────────────────────────────────────────────────────────────────
# Meraki -- Alerts
# ──────────────────────────────────────────────────────────────────────────


class ListAlertsParams(_MerakiScoped):
    network_id: str = Field("", description="Optional network id filter.")


class Alert(sdl.Entity):
    id: str = ""
    title: str = ""
    category: str = ""
    severity: str = ""
    occurred_at: str = ""


class AlertList(sdl.Entity):
    id: str = "alert_list"
    title: str = ""
    items: list[Alert] = Field(default_factory=list)


class CreateAlertWebhookParams(_MerakiScoped):
    network_id: str = Field(..., description="Network id to attach the webhook to.")
    url: str = Field(..., description="HTTPS URL Meraki should POST alerts to.")
    name: str = Field("Imperal alert webhook", description="Friendly name for this webhook receiver.")


class WebhookResult(sdl.Entity):
    id: str = ""
    title: str = ""
    url: str = ""


# ──────────────────────────────────────────────────────────────────────────
# Bulk + Audit (Ярус 3)
# ──────────────────────────────────────────────────────────────────────────


class BulkUpdateDestinationListsParams(_UmbrellaScoped):
    destination_list_ids: list[str] = Field(..., description="Destination list ids to act on.")
    access: str = Field(..., description="New access value: allow or block.")


class BulkActionOutcome(sdl.Entity):
    id: str = ""
    title: str = ""
    ok: bool = True
    error: str = ""


class BulkActionResult(sdl.Entity):
    id: str = "bulk_action_result"
    title: str = ""
    items: list[BulkActionOutcome] = Field(default_factory=list)


class BulkRebootAppliancesParams(_MerakiScoped):
    serials: list[str] = Field(..., description="Serial numbers of the appliances to reboot.")


class AuditSecureAccessParams(BaseModel):
    umbrella_connection_id: str = Field("", description="Which Umbrella connection to audit. Omit if only one is connected.")
    meraki_connection_id: str = Field("", description="Which Meraki connection to audit. Omit if only one is connected.")


class AuditFinding(sdl.Entity):
    id: str = ""
    title: str = ""
    severity: str = ""  # "critical" | "high" | "medium" | "low" | "info"
    detail: str = ""


class AuditReport(sdl.Entity):
    id: str = "audit_report"
    title: str = ""
    unassigned_destination_lists: int = 0
    offline_roaming_computers: int = 0
    offline_appliances: int = 0
    recent_alerts_24h: int = 0
    findings: list[AuditFinding] = Field(default_factory=list)
