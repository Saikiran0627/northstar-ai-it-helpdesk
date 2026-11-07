"""Shared data models for the help desk agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class KnowledgeChunk:
    doc_id: str
    title: str
    source: str
    text: str
    score: float = 0.0


@dataclass(frozen=True)
class ToolResult:
    name: str
    success: bool
    data: dict[str, Any]
    latency_ms: float


@dataclass
class TraceStep:
    stage: str
    action: str
    observation: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now_iso)


@dataclass
class PendingTicket:
    title: str
    description: str
    priority: str
    requester: str = "employee@northstar.example"


@dataclass
class AgentResponse:
    message: str
    trace: list[TraceStep]
    citations: list[KnowledgeChunk] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    pending_ticket: PendingTicket | None = None
    created_ticket_id: int | None = None
    latency_ms: float = 0.0
