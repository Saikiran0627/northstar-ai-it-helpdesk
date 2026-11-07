"""Streamlit entry point for the Northstar Technologies AI IT Help Desk."""

from __future__ import annotations

from uuid import uuid4

import pandas as pd
import streamlit as st

from northstar_helpdesk.agent import HelpDeskAgent
from northstar_helpdesk.config import load_settings
from northstar_helpdesk.evaluation import run_evaluations
from northstar_helpdesk.knowledge_base import KnowledgeBase
from northstar_helpdesk.llm import ClaudeClient
from northstar_helpdesk.models import PendingTicket
from northstar_helpdesk.ticket_store import TicketStore


@st.cache_resource
def get_services() -> tuple[HelpDeskAgent, TicketStore, bool]:
    settings = load_settings()
    store = TicketStore(settings.db_path)
    kb = KnowledgeBase(settings.knowledge_dir)
    llm = ClaudeClient(settings)
    return HelpDeskAgent(kb, llm, store), store, settings.llm_configured


def init_session() -> None:
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi, I am Northstar Technologies' AI IT Help Desk. "
                    "Tell me what is happening and I will search internal support docs, "
                    "check simulated service status when useful, and ask before creating tickets."
                ),
            }
        ]
    if "pending_ticket" not in st.session_state:
        st.session_state.pending_ticket = None
    if "last_trace" not in st.session_state:
        st.session_state.last_trace = []


def render_trace() -> None:
    with st.expander("Agent execution trace", expanded=True):
        if not st.session_state.last_trace:
            st.info("No trace yet. Send a message to see retrieval and tool activity.")
            return
        trace_rows = [
            {
                "time": step.timestamp,
                "stage": step.stage,
                "action": step.action,
                "observation": step.observation,
                "metadata": step.metadata,
            }
            for step in st.session_state.last_trace
        ]
        st.dataframe(pd.DataFrame(trace_rows), use_container_width=True)


def render_tickets(store: TicketStore) -> None:
    st.subheader("Support tickets")
    tickets = store.list_tickets()
    if tickets:
        st.dataframe(pd.DataFrame(tickets), use_container_width=True)
    else:
        st.info("No tickets have been created.")


def render_evaluations(agent: HelpDeskAgent, store: TicketStore) -> None:
    st.subheader("Evaluation dashboard")
    if st.button("Run local evaluation suite"):
        results = run_evaluations(agent)
        for result in results:
            store.log_evaluation(result)
        st.success(f"Ran {len(results)} evaluation cases.")

    evaluations = store.list_evaluations()
    if evaluations:
        frame = pd.DataFrame(evaluations)
        pass_rate = frame["passed"].mean() * 100
        avg_latency = frame["latency_ms"].mean()
        avg_tool_success = frame["tool_success_rate"].mean() * 100
        col1, col2, col3 = st.columns(3)
        col1.metric("Pass rate", f"{pass_rate:.0f}%")
        col2.metric("Avg latency", f"{avg_latency:.0f} ms")
        col3.metric("Tool success", f"{avg_tool_success:.0f}%")
        st.dataframe(frame, use_container_width=True)
    else:
        st.info("Run the local evaluation suite to populate quality metrics.")


def main() -> None:
    st.set_page_config(page_title="Northstar AI IT Help Desk", layout="wide")
    init_session()
    agent, store, llm_configured = get_services()

    st.title("Northstar Technologies AI IT Help Desk")
    st.caption(
        "Local RAG over IT policy docs, simulated tools, SQLite tickets, confirmation gates, and trace logging."
    )

    if not llm_configured:
        st.warning(
            "Claude/Azure settings were not found in .env, so the app is using deterministic local fallback responses."
        )

    chat_col, side_col = st.columns([0.62, 0.38], gap="large")
    with chat_col:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("Ask for IT help...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            response = agent.respond(
                user_message=prompt,
                history=st.session_state.messages[:-1],
                conversation_id=st.session_state.conversation_id,
                pending_ticket=st.session_state.pending_ticket,
            )
            st.session_state.last_trace = response.trace
            st.session_state.pending_ticket = response.pending_ticket
            if response.created_ticket_id:
                st.session_state.pending_ticket = None

            st.session_state.messages.append({"role": "assistant", "content": response.message})
            with st.chat_message("assistant"):
                st.markdown(response.message)
                if response.citations:
                    st.caption(
                        "Sources: "
                        + ", ".join(f"{doc.title} ({doc.source})" for doc in response.citations)
                    )

    with side_col:
        render_trace()
        if isinstance(st.session_state.pending_ticket, PendingTicket):
            st.info(
                "Ticket draft waiting for confirmation: "
                f"{st.session_state.pending_ticket.title} "
                f"({st.session_state.pending_ticket.priority} priority)."
            )
        render_tickets(store)
        render_evaluations(agent, store)


if __name__ == "__main__":
    main()
