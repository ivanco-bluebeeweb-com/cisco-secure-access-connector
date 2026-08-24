"""Chat functions for Cisco Umbrella / Secure Access: destination lists,
policies, identities (networks/roaming computers/virtual appliances), ZTNA
private resources, and reporting. Built on cisco_client.py / schemas.py,
following the same shape as Zscaler Connector's handlers_zia.py.
"""
from __future__ import annotations

import uuid

from imperal_sdk import ActionResult

import cisco_client as cc
from app import chat
from handlers_connection import _authed_umbrella
from schemas import (
    ListDestinationListsParams, DestinationList, DestinationListList,
    GetDestinationListParams, CreateDestinationListParams,
    UpdateDestinationListParams, DeleteDestinationListParams,
    AddDestinationListEntryParams, RemoveDestinationListEntryParams,
    DeleteResult,
    ListPoliciesParams, Policy, PolicyList, GetPolicyParams,
    ListNetworksParams, UmbrellaNetwork, UmbrellaNetworkList,
    ListRoamingComputersParams, RoamingComputer, RoamingComputerList,
    ListVirtualAppliancesParams, VirtualAppliance, VirtualApplianceList,
    ListPrivateResourcesParams, PrivateResource, PrivateResourceList,
    GetPrivateResourceParams, CreatePrivateResourceParams,
    UpdatePrivateResourceParams, DeletePrivateResourceParams,
    ListActivityParams, ActivityEntry, ActivityList,
    GetTopReportParams, TopReportRow, TopReportResult,
)


@chat.function(
    "list_destination_lists",
    "List Umbrella/Secure Access destination lists (domain allow/block lists).",
    action_type="read",
    data_model=DestinationListList,
)
async def list_destination_lists(ctx, params: ListDestinationListsParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    ok, data = await cc.umbrella_request(ctx, conn, token, "GET", "/policies/v2/destinationlists")
    if not ok:
        return data
    items = [
        DestinationList(
            id=str(d.get("id", "")), title=d.get("name", ""),
            access=d.get("access", ""), entry_count=d.get("meta", {}).get("total", 0),
            is_global=d.get("isGlobal", False),
        )
        for d in (data if isinstance(data, list) else data.get("data", []))
    ]
    return ActionResult(success=True, data=DestinationListList(title=f"{len(items)} destination list(s)", items=items))


@chat.function(
    "get_destination_list",
    "Read one destination list in full.",
    action_type="read",
    data_model=DestinationList,
)
async def get_destination_list(ctx, params: GetDestinationListParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    ok, data = await cc.umbrella_request(ctx, conn, token, "GET", f"/policies/v2/destinationlists/{params.destination_list_id}")
    if not ok:
        return data
    return ActionResult(success=True, data=DestinationList(
        id=str(data.get("id", "")), title=data.get("name", ""),
        access=data.get("access", ""), entry_count=data.get("meta", {}).get("total", 0),
        is_global=data.get("isGlobal", False),
    ))


@chat.function(
    "create_destination_list",
    "Create a new destination list.",
    action_type="write",
    data_model=DestinationList,
)
async def create_destination_list(ctx, params: CreateDestinationListParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    body = {"name": params.name, "access": params.access, "destinations": []}
    ok, data = await cc.umbrella_request(ctx, conn, token, "POST", "/policies/v2/destinationlists", json_body=body)
    if not ok:
        return data
    return ActionResult(success=True, data=DestinationList(
        id=str(data.get("id", "")), title=data.get("name", params.name), access=params.access,
    ))


@chat.function(
    "update_destination_list",
    "Update an existing destination list's name.",
    action_type="write",
    data_model=DestinationList,
)
async def update_destination_list(ctx, params: UpdateDestinationListParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    body = {}
    if params.name:
        body["name"] = params.name
    ok, data = await cc.umbrella_request(ctx, conn, token, "PATCH", f"/policies/v2/destinationlists/{params.destination_list_id}", json_body=body)
    if not ok:
        return data
    return ActionResult(success=True, data=DestinationList(id=params.destination_list_id, title=params.name or "(updated)"))


@chat.function(
    "delete_destination_list",
    "Permanently delete a destination list. Cannot be undone.",
    action_type="write",
    data_model=DeleteResult,
)
async def delete_destination_list(ctx, params: DeleteDestinationListParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    ok, data = await cc.umbrella_request(ctx, conn, token, "DELETE", f"/policies/v2/destinationlists/{params.destination_list_id}")
    if not ok:
        return data
    return ActionResult(success=True, data=DeleteResult(id=params.destination_list_id, title="Deleted", deleted=True))


@chat.function(
    "add_destination_list_entry",
    "Add domains/URLs/IPs to a destination list.",
    action_type="write",
    data_model=DestinationList,
)
async def add_destination_list_entry(ctx, params: AddDestinationListEntryParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    body = [{"destination": d, "comment": ""} for d in params.destinations]
    ok, data = await cc.umbrella_request(ctx, conn, token, "POST", f"/policies/v2/destinationlists/{params.destination_list_id}/destinations", json_body=body)
    if not ok:
        return data
    return ActionResult(success=True, data=DestinationList(id=params.destination_list_id, title="Entries added"))


@chat.function(
    "remove_destination_list_entry",
    "Remove domains/URLs/IPs from a destination list.",
    action_type="write",
    data_model=DestinationList,
)
async def remove_destination_list_entry(ctx, params: RemoveDestinationListEntryParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    ok, data = await cc.umbrella_request(
        ctx, conn, token, "DELETE",
        f"/policies/v2/destinationlists/{params.destination_list_id}/destinations/remove",
        json_body=params.destinations,
    )
    if not ok:
        return data
    return ActionResult(success=True, data=DestinationList(id=params.destination_list_id, title="Entries removed"))


@chat.function(
    "list_policies",
    "List Umbrella/Secure Access policies (destination-list + identity bindings).",
    action_type="read",
    data_model=PolicyList,
)
async def list_policies(ctx, params: ListPoliciesParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    ok, data = await cc.umbrella_request(ctx, conn, token, "GET", "/policies/v2/dnspolicies")
    if not ok:
        return data
    items = [
        Policy(id=str(p.get("policyId", "")), title=p.get("policyName", ""),
               priority=p.get("priority", 0), identity_count=len(p.get("identities", [])))
        for p in (data if isinstance(data, list) else data.get("data", []))
    ]
    return ActionResult(success=True, data=PolicyList(title=f"{len(items)} polic(y/ies)", items=items))


@chat.function(
    "get_policy",
    "Read one policy in full.",
    action_type="read",
    data_model=Policy,
)
async def get_policy(ctx, params: GetPolicyParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    ok, data = await cc.umbrella_request(ctx, conn, token, "GET", f"/policies/v2/dnspolicies/{params.policy_id}")
    if not ok:
        return data
    return ActionResult(success=True, data=Policy(
        id=str(data.get("policyId", "")), title=data.get("policyName", ""),
        priority=data.get("priority", 0), identity_count=len(data.get("identities", [])),
    ))


@chat.function(
    "list_umbrella_networks",
    "List Umbrella network identities (fixed-IP sites).",
    action_type="read",
    data_model=UmbrellaNetworkList,
)
async def list_umbrella_networks(ctx, params: ListNetworksParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    ok, data = await cc.umbrella_request(ctx, conn, token, "GET", "/deployments/v2/networks")
    if not ok:
        return data
    items = [
        UmbrellaNetwork(id=str(n.get("originId", "")), title=n.get("name", ""),
                         ip_address=n.get("ipAddress", ""), status=n.get("status", ""))
        for n in (data if isinstance(data, list) else data.get("data", []))
    ]
    return ActionResult(success=True, data=UmbrellaNetworkList(title=f"{len(items)} network(s)", items=items))


@chat.function(
    "list_roaming_computers",
    "List Umbrella roaming client computers.",
    action_type="read",
    data_model=RoamingComputerList,
)
async def list_roaming_computers(ctx, params: ListRoamingComputersParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    query = {"search": params.search} if params.search else None
    ok, data = await cc.umbrella_request(ctx, conn, token, "GET", "/deployments/v2/roamingcomputers", query=query)
    if not ok:
        return data
    items = [
        RoamingComputer(
            id=str(rc.get("originId", "")), title=rc.get("hostname") or rc.get("name", ""),
            os_version=rc.get("osVersionName", ""), status=rc.get("status", ""),
            last_sync=str(rc.get("lastSync", "")),
        )
        for rc in (data if isinstance(data, list) else data.get("data", []))
    ]
    return ActionResult(success=True, data=RoamingComputerList(title=f"{len(items)} roaming computer(s)", items=items))


@chat.function(
    "list_virtual_appliances",
    "List Umbrella Virtual Appliances.",
    action_type="read",
    data_model=VirtualApplianceList,
)
async def list_virtual_appliances(ctx, params: ListVirtualAppliancesParams) -> ActionResult:
    auth = await _authed_umbrella(ctx, params.connection_id)
    if isinstance(auth, ActionResult):
        return auth
    conn, token = auth
    ok, data = await cc.umbrella_request(ctx, conn, token, "GET", "/deployments/v2/virtualappliances")
    if not ok:
        return data
    items = [
        VirtualAppliance(id=str(va.get("originId", "")), title=va.get("name", ""), status=va.get("status", ""))
        for va in (data if isinstance(data, list) else data.get("data", []))
    ]
    return ActionResult(success=True, data=VirtualApplianceList(title=f"{len(items)} virtual appliance(s)", items=items))
