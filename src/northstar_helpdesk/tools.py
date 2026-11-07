"""Simulated IT operations tools."""

from __future__ import annotations

import time

from northstar_helpdesk.models import PendingTicket, ToolResult
from northstar_helpdesk.ticket_store import TicketStore


SERVICE_STATUS = {
    "vpn": {
        "status": "degraded",
        "summary": "Northstar VPN gateway vpn-us-east-2 is experiencing elevated reconnects.",
        "updated": "2026-11-07T19:55:00Z",
    },
    "email": {
        "status": "operational",
        "summary": "Microsoft 365 mail flow is healthy.",
        "updated": "2026-11-07T19:40:00Z",
    },
    "identity": {
        "status": "operational",
        "summary": "SSO and MFA services are healthy.",
        "updated": "2026-11-07T19:45:00Z",
    },
    "wifi": {
        "status": "operational",
        "summary": "Corporate wireless controllers report normal service.",
        "updated": "2026-11-07T19:35:00Z",
    },
}


def check_service_status(service_name: str) -> ToolResult:
    started = time.perf_counter()
    key = service_name.lower().strip()
    data = SERVICE_STATUS.get(
        key,
        {
            "status": "unknown",
            "summary": f"No simulated status feed exists for {service_name}.",
            "updated": "unknown",
        },
    )
    return ToolResult(
        name="check_service_status",
        success=data["status"] != "unknown",
        data={"service": key, **data},
        latency_ms=(time.perf_counter() - started) * 1000,
    )


def create_support_ticket(ticket: PendingTicket, store: TicketStore) -> ToolResult:
    started = time.perf_counter()
    ticket_id = store.create_ticket(
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        requester=ticket.requester,
    )
    return ToolResult(
        name="create_support_ticket",
        success=True,
        data={"ticket_id": ticket_id, "priority": ticket.priority, "status": "open"},
        latency_ms=(time.perf_counter() - started) * 1000,
    )
