"""Panel UI -- connections list/connect forms (Umbrella + Meraki, two
independent sections) + Umbrella/Meraki navigation.

SIDEBAR CONTENT -- NO CARDS ANYWHERE, per ~/UI_INTERFACE_STANDARD.md's
"left sidebar, no decorated cards" rule (same convention as Zscaler
Connector's / CircleCI Connector's panels.py). Every section is a plain
ui.Stack, content stacked vertically, sections separated by ui.Divider()
-- no Card border/background/shadow anywhere in this slot. Disconnect
lives only in the "App settings" screen (panels_settings.py). The one
secondary "App settings" button is always the LAST element at the
bottom of the sidebar.

PER ~/UI_INTERFACE_STANDARD.md (2026-08-21 addendum): every Input carries
its own visible label (rendered here as a sibling ui.Text caption, since
ui.Input/ui.Password/ui.Select take no label= kwarg -- lesson learned
from Zscaler Connector's deploy rejection), the placeholder text is
always contextually specific to what's being entered, the connect
form's container is stretched full-width, and its content fills that
width. The "How do I set this up?" walkthrough lives ONLY in the help
panel below -- never duplicated as static sidebar text.

Implements UI_COMPONENT_PLAN.md §1 exactly (built alongside that plan,
not after -- APP_PREPARATION_STANDARD.md §9).
"""
from __future__ import annotations

from imperal_sdk import ui

import handlers_connection as h
from app import ext


def _connect_help_panel_body() -> ui.UINode:
    return ui.Stack(direction="v", gap=3, children=[
        ui.Text("Umbrella / Secure Access:", variant="body"),
        ui.Text("1. Sign in to the Umbrella dashboard (admin.umbrella.com)."),
        ui.Text("2. Go to Admin > API Keys > Add > Umbrella Management/Reporting."),
        ui.Text("3. Copy the Key and Secret shown."),
        ui.Divider(),
        ui.Text("Meraki:", variant="body"),
        ui.Text("1. Sign in to the Meraki dashboard (dashboard.meraki.com)."),
        ui.Text("2. Go to My profile (top-right) > API access > Generate API key."),
        ui.Text("3. Copy the key -- Meraki shows it only once."),
        ui.Divider(),
        ui.Alert(
            title="Two independent connections",
            message=(
                "Umbrella/Secure Access and Meraki are separate Cisco products "
                "with separate credentials. Connect either one, or both -- "
                "neither is required for the other to work."
            ),
            type="info",
        ),
    ])


@ext.panel("cisco_connect_help", slot="center", center_overlay=True)
async def cisco_connect_help_panel(ctx) -> ui.UINode:
    return _connect_help_panel_body()


def _connection_row(c) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="start", children=[
        ui.Text(c.title, variant="body"),
        ui.Text(c.detail, variant="caption"),
    ])


def _connections_section(items) -> ui.UINode:
    if not items:
        return ui.Empty(message="No Cisco Umbrella/Meraki connections yet.", icon="shield")
    children: list[ui.UINode] = []
    for i, c in enumerate(items):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, children=children)


def _connect_umbrella_form() -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("Connect Umbrella / Secure Access", variant="body"),
        ui.Form(
            action="connect_umbrella",
            submit_label="Verify and connect",
            children=[
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("API Key", variant="caption"),
                    ui.Input(param_name="api_key", placeholder="Umbrella Management/Reporting API key"),
                ]),
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("API Secret", variant="caption"),
                    ui.Password(param_name="api_secret", placeholder="Umbrella API secret"),
                ]),
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Label (optional)", variant="caption"),
                    ui.Input(param_name="label", placeholder="e.g. Acme Corp Umbrella"),
                ]),
            ],
        ),
    ])


def _connect_meraki_form() -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("Connect Meraki", variant="body"),
        ui.Form(
            action="connect_meraki",
            submit_label="Verify and connect",
            children=[
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Meraki API Key", variant="caption"),
                    ui.Password(param_name="meraki_api_key", placeholder="Meraki Dashboard API key"),
                ]),
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Organization ID (optional)", variant="caption"),
                    ui.Input(param_name="organization_id", placeholder="Leave empty to auto-resolve the first organization"),
                ]),
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Label (optional)", variant="caption"),
                    ui.Input(param_name="label", placeholder="e.g. Acme Corp Meraki"),
                ]),
            ],
        ),
    ])


@ext.panel("cisco_sidebar", slot="left")
async def cisco_sidebar_panel(ctx) -> ui.UINode:
    result = await h.list_connections(ctx, h.NoParams())
    items = result.data.items if result.success and result.data else []

    children: list[ui.UINode] = [
        ui.Button(
            "How do I set this up?", variant="ghost", size="sm", icon="HelpCircle",
            on_click=ui.Call("__panel__cisco_connect_help"),
        ),
    ]

    if items:
        children.append(ui.Divider())
        children.append(ui.Text("Connections", variant="heading"))
        children.append(_connections_section(items))
        children.append(ui.Divider())
        children.append(ui.Text("Navigate", variant="heading"))
        children.append(ui.ListItem(
            id="umbrella", title="Umbrella / Secure Access", subtitle="Destination lists, policies, ZTNA",
            on_click=ui.Call("__panel__cisco_umbrella_overview"),
        ))
        children.append(ui.ListItem(
            id="meraki", title="Meraki SD-WAN", subtitle="Networks, uplinks, appliances",
            on_click=ui.Call("__panel__cisco_meraki_overview"),
        ))
    else:
        children.append(ui.Divider())

    children.append(_connect_umbrella_form())
    children.append(ui.Divider())
    children.append(_connect_meraki_form())
    children.append(ui.Divider())
    children.append(ui.Button(
        "App settings", variant="ghost", size="sm", icon="Settings",
        on_click=ui.Call("__panel__cisco_settings"),
    ))

    return ui.Stack(direction="v", gap=3, align="stretch", children=children)


@ext.panel("cisco_center", slot="center")
async def cisco_center_panel(ctx) -> ui.UINode:
    result = await h.list_connections(ctx, h.NoParams())
    items = result.data.items if result.success and result.data else []
    if not items:
        return ui.Empty(
            message="Connect your Cisco Umbrella/Secure Access or Meraki organization first.",
            icon="shield",
        )
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("Cisco Secure Access", variant="heading"),
        ui.Text(
            "Ask Webbee to list destination lists, policies, networks, appliance health, or run a health audit.",
            variant="caption",
        ),
    ])
