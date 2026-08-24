"""The single 'App settings' screen (center slot) -- connection management
(disconnect per Umbrella/Meraki connection) for Cisco Secure Access
Connector. Split out of panels.py per the same convention as Zscaler
Connector's / CircleCI Connector's panels_settings.py.

Per ~/UI_INTERFACE_STANDARD.md: the left sidebar never wraps the connect
form in a Card, and disconnect (never exposed in the sidebar itself) lives
here, one row per connected Umbrella/Meraki connection. The one secondary
"App settings" button sits LAST at the bottom of the sidebar.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers_connection as h


def _connection_row(c) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="start", children=[
        ui.Text(c.title, variant="body"),
        ui.Text(c.detail, variant="caption"),
        ui.Button(
            "Disconnect", variant="danger", size="sm",
            on_click=ui.Call("disconnect_connection", {"connection_id": c.id, "kind": c.kind}),
        ),
    ])


def _connections_section(items) -> ui.UINode:
    if not items:
        return ui.Stack(direction="v", gap=1, children=[
            ui.Text("Connections", variant="heading"),
            ui.Text("No Umbrella or Meraki connections yet.", variant="caption"),
        ])
    children: list[ui.UINode] = [ui.Text("Connections", variant="heading")]
    for i, c in enumerate(items):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, align="start", children=children)


@ext.panel("cisco_settings", slot="center", center_overlay=True)
async def cisco_settings_panel(ctx) -> ui.UINode:
    result = await h.list_connections(ctx, h.NoParams())
    items = result.data.items if result.success and result.data else []
    return ui.Stack(direction="v", gap=3, align="start", children=[
        ui.Text("App settings", variant="heading"),
        _connections_section(items),
    ])
