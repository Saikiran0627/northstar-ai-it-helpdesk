from __future__ import annotations

from pathlib import Path

import pytest

from northstar_helpdesk.agent import HelpDeskAgent
from northstar_helpdesk.config import Settings
from northstar_helpdesk.knowledge_base import KnowledgeBase
from northstar_helpdesk.llm import ClaudeClient
from northstar_helpdesk.ticket_store import TicketStore


@pytest.fixture()
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        claude_api_endpoint=None,
        claude_api_key=None,
        claude_model=None,
        claude_api_version=None,
        db_path=tmp_path / "helpdesk.db",
        knowledge_dir=Path(__file__).resolve().parents[1] / "data" / "knowledge",
    )


@pytest.fixture()
def agent(test_settings: Settings) -> HelpDeskAgent:
    store = TicketStore(test_settings.db_path)
    kb = KnowledgeBase(test_settings.knowledge_dir)
    llm = ClaudeClient(test_settings)
    return HelpDeskAgent(kb, llm, store)
