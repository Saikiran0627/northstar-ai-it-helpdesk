# VPN Remote Access Troubleshooting

Northstar Technologies employees use the Northstar SecureConnect VPN client for remote access to internal systems.

Common symptoms:
- VPN tunnel connects and then disconnects repeatedly.
- Authentication succeeds but internal applications are unreachable.
- Video calls or client presentations become unstable while the VPN is active.

Recommended steps:
1. Move to a stable network. Prefer wired Ethernet or a strong private Wi-Fi network over public hotspots.
2. Restart the SecureConnect client and reconnect. This refreshes the tunnel and MFA session.
3. If reconnects continue, switch from the default `vpn-us-east-2` gateway to `vpn-us-west-1`.
4. Pause bandwidth-heavy sync tools such as cloud backups while presenting.
5. If the user has an urgent business event, check VPN service status and prepare a high-priority support ticket for confirmation.

Never ask an employee to disable endpoint protection or share MFA codes.
