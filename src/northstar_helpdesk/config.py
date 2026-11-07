"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_KNOWLEDGE_DIR = ROOT_DIR / "data" / "knowledge"
DEFAULT_DB_PATH = ROOT_DIR / "data" / "helpdesk.db"


@dataclass(frozen=True)
class Settings:
    claude_api_endpoint: str | None
    claude_api_key: str | None
    claude_model: str | None
    claude_api_version: str | None
    db_path: Path
    knowledge_dir: Path

    @property
    def llm_configured(self) -> bool:
        return all(
            [
                self.claude_api_endpoint,
                self.claude_api_key,
                self.claude_model,
            ]
        )


def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")

    db_path = Path(os.getenv("HELPDESK_DB_PATH", str(DEFAULT_DB_PATH)))
    if not db_path.is_absolute():
        db_path = ROOT_DIR / db_path

    knowledge_dir = Path(os.getenv("HELPDESK_KNOWLEDGE_DIR", str(DEFAULT_KNOWLEDGE_DIR)))
    if not knowledge_dir.is_absolute():
        knowledge_dir = ROOT_DIR / knowledge_dir

    return Settings(
        claude_api_endpoint=os.getenv("CLAUDE_API_ENDPOINT"),
        claude_api_key=os.getenv("CLAUDE_API_KEY"),
        claude_model=os.getenv("CLAUDE_MODEL"),
        claude_api_version=os.getenv("CLAUDE_API_VERSION"),
        db_path=db_path,
        knowledge_dir=knowledge_dir,
    )
