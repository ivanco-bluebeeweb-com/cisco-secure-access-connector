"""Cisco Secure Access Connector -- app + extension setup.

Two independent BYOK auth surfaces under one product umbrella, same
convention as Zscaler Connector's ZIA/ZPA split:
  - Umbrella / Secure Access: OAuth2 client_credentials (api_key/api_secret).
  - Meraki: static X-Cisco-Meraki-API-Key header.

See PREPARATION.md for the full why.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "cisco-secure-access-connector",
    version="0.1.0",
    display_name="Cisco Secure Access",
    icon="icon.svg",
    description=(
        "Connect your own Cisco Umbrella/Secure Access (DNS/SIG/ZTNA) and/or "
        "Meraki (SD-WAN) organization to manage destination lists, policies, "
        "identities, ZTNA private resources, reporting, networks, appliance "
        "health, VPN topology and alerts from Imperal -- plus bulk operations "
        "and a tenant health audit. Uses your own Umbrella API key/secret "
        "and/or Meraki API key -- nothing is hosted or proxied by Imperal "
        "beyond the request itself. Note: Duo (MFA) is a separate product "
        "and out of scope for this first release."
    ),
)

ext.secret("cisco_secure_access_connections", description="Stored Umbrella/Meraki connection credentials (JSON array)")

chat = ChatExtension(
    ext,
    tool_name="cisco_secure_access",
    description="Manage Cisco Umbrella/Secure Access and Meraki SD-WAN from Imperal.",
)
