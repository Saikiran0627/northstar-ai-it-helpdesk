"""Agent orchestration for the Northstar IT Help Desk."""

from __future__ import annotations

import time
from uuid import uuid4

from northstar_helpdesk.knowledge_base import KnowledgeBase
from northstar_helpdesk.llm import ClaudeClient
from northstar_helpdesk.models import AgentResponse, PendingTicket, TraceStep
from northstar_helpdesk.security import assess_user_message
from northstar_helpdesk.ticket_store import TicketStore
from northstar_helpdesk.tools import check_service_status, create_support_ticket


CONFIRMATION_WORDS = {"yes", "y", "confirm", "approved", "approve", "please create", "create it"}
NEGATIVE_WORDS = {"no", "n", "cancel", "do not", "don't", "not now"}


class HelpDeskAgent:
    def __init__(self, kb: KnowledgeBase, llm: ClaudeClient, store: TicketStore):
        self.kb = kb
        self.llm = llm
        self.store = store

    def respond(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        conversation_id: str | None = None,
        pending_ticket: PendingTicket | None = None,
    ) -> AgentResponse:
        started = time.perf_counter()
        history = history or []
        conversation_id = conversation_id or str(uuid4())
        trace: list[TraceStep] = []
        tool_results = []
        citations = []

        safety = assess_user_message(user_message)
        trace.append(
            TraceStep(
                stage="input_screening",
                action="screen_user_message",
                observation="Blocked unsafe instruction" if not safety.allowed else "Message passed safety checks",
            )
        )
        if not safety.allowed:
            response = AgentResponse(message=str(safety.warning), trace=trace)
            self.store.log_trace(conversation_id, trace)
            return response

        normalized = user_message.lower().strip()
        if pending_ticket and self._is_confirmation(normalized):
            tool_result = create_support_ticket(pending_ticket, self.store)
            tool_results.append(tool_result)
            trace.append(
                TraceStep(
                    stage="tool_call",
                    action="create_support_ticket",
                    observation=f"Created ticket {tool_result.data['ticket_id']} after explicit confirmation",
                    metadata=tool_result.data,
                )
            )
            message = (
                f"Confirmed. I created support ticket #{tool_result.data['ticket_id']} "
                f"with {tool_result.data['priority']} priority. I created it only after your confirmation."
            )
            response = AgentResponse(
                message=message,
                trace=trace,
                tool_results=tool_results,
                created_ticket_id=int(tool_result.data["ticket_id"]),
                latency_ms=(time.perf_counter() - started) * 1000,
            )
            self.store.log_trace(conversation_id, trace)
            return response

        if pending_ticket and self._is_rejection(normalized):
            trace.append(
                TraceStep(
                    stage="ticket_confirmation",
                    action="cancel_pending_ticket",
                    observation="User declined ticket creation",
                )
            )
            response = AgentResponse(
                message="No problem. I did not create a ticket. We can keep troubleshooting here.",
                trace=trace,
                latency_ms=(time.perf_counter() - started) * 1000,
            )
            self.store.log_trace(conversation_id, trace)
            return response

        intent = self._classify_intent(normalized)
        trace.append(
            TraceStep(
                stage="intent_classification",
                action="classify_request",
                observation=f"Detected intent: {intent}",
            )
        )

        if intent == "clarify":
            trace.append(
                TraceStep(
                    stage="clarification",
                    action="ask_follow_up",
                    observation="Request lacked enough troubleshooting detail",
                )
            )
            response = AgentResponse(
                message=(
                    "I can help. Which system is affected, what error do you see, "
                    "and are you remote, in-office, or on guest Wi-Fi?"
                ),
                trace=trace,
                latency_ms=(time.perf_counter() - started) * 1000,
            )
            self.store.log_trace(conversation_id, trace)
            return response

        citations = self.kb.search(user_message, limit=3)
        trace.append(
            TraceStep(
                stage="retrieval",
                action="search_knowledge_base",
                observation=f"Retrieved {len(citations)} relevant documents",
                metadata={"documents": [doc.title for doc in citations]},
            )
        )

        service = self._service_from_message(normalized)
        if service:
            status = check_service_status(service)
            tool_results.append(status)
            trace.append(
                TraceStep(
                    stage="tool_call",
                    action="check_service_status",
                    observation=f"Checked simulated {service} service status",
                    metadata=status.data,
                )
            )

        answer = self.llm.generate_answer(
            user_message=user_message,
            history=history,
            citations=citations,
            tool_results=tool_results,
        )

        next_ticket = None
        if self._should_offer_ticket(normalized, tool_results):
            priority = "high" if self._is_urgent(normalized) else "normal"
            next_ticket = PendingTicket(
                title=self._ticket_title(normalized),
                description=f"Employee reported: {user_message}",
                priority=priority,
            )
            answer += (
                "\n\nIf you want me to create a support ticket, reply `confirm`. "
                f"Proposed ticket: {next_ticket.title} ({next_ticket.priority} priority)."
            )
            trace.append(
                TraceStep(
                    stage="ticket_confirmation",
                    action="prepare_ticket_draft",
                    observation="Prepared a ticket draft and requested confirmation before creation",
                    metadata={"title": next_ticket.title, "priority": next_ticket.priority},
                )
            )

        trace.append(
            TraceStep(
                stage="generation",
                action="generate_grounded_answer",
                observation="Generated answer from retrieved documents and tool outputs",
            )
        )
        response = AgentResponse(
            message=answer,
            trace=trace,
            citations=citations,
            tool_results=tool_results,
            pending_ticket=next_ticket,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
        self.store.log_trace(conversation_id, trace)
        return response

    def _classify_intent(self, normalized: str) -> str:
        if len(normalized.split()) < 4 and "vpn" not in normalized:
            return "clarify"
        if any(word in normalized for word in ["ticket", "issue", "broken", "disconnect", "error", "help"]):
            return "troubleshoot"
        return "answer"

    def _service_from_message(self, normalized: str) -> str | None:
        service_terms = {
            "vpn": ["vpn", "remote access", "globalprotect", "tunnel"],
            "email": ["email", "outlook", "mail"],
            "identity": ["mfa", "sso", "password", "login", "okta"],
            "wifi": ["wifi", "wi-fi", "wireless"],
        }
        for service, terms in service_terms.items():
            if any(term in normalized for term in terms):
                return service
        return None

    def _should_offer_ticket(self, normalized: str, tool_results: list) -> bool:
        explicit_ticket = "ticket" in normalized or "escalate" in normalized
        urgent_issue = self._is_urgent(normalized) and any(result.name == "check_service_status" for result in tool_results)
        degraded_service = any(result.data.get("status") == "degraded" for result in tool_results)
        return explicit_ticket or urgent_issue or degraded_service

    def _is_urgent(self, normalized: str) -> bool:
        return any(term in normalized for term in ["urgent", "presentation", "client", "deadline", "30 minutes"])

    def _ticket_title(self, normalized: str) -> str:
        if "vpn" in normalized:
            return "VPN disconnecting during remote work"
        if "email" in normalized or "outlook" in normalized:
            return "Email service issue"
        if "mfa" in normalized or "login" in normalized:
            return "Identity access issue"
        return "Employee IT support request"

    def _is_confirmation(self, normalized: str) -> bool:
        return normalized in CONFIRMATION_WORDS or any(phrase in normalized for phrase in CONFIRMATION_WORDS)

    def _is_rejection(self, normalized: str) -> bool:
        return normalized in NEGATIVE_WORDS or any(phrase in normalized for phrase in NEGATIVE_WORDS)
