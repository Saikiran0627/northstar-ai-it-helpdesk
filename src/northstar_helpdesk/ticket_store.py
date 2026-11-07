"""SQLite persistence for tickets, traces, and evaluation runs."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from northstar_helpdesk.models import TraceStep, utc_now_iso


class TicketStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    requester TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS execution_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    action TEXT NOT NULL,
                    observation TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    tool_success_rate REAL NOT NULL,
                    answer_score REAL NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def create_ticket(
        self,
        *,
        title: str,
        description: str,
        priority: str,
        requester: str,
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO tickets (title, description, priority, requester, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, description, priority, requester, utc_now_iso()),
            )
            return int(cursor.lastrowid)

    def list_tickets(self, limit: int = 25) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM tickets ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def log_trace(self, conversation_id: str, steps: list[TraceStep]) -> None:
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO execution_steps (
                    conversation_id, stage, action, observation, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        conversation_id,
                        step.stage,
                        step.action,
                        step.observation,
                        json.dumps(step.metadata, sort_keys=True),
                        step.timestamp,
                    )
                    for step in steps
                ],
            )

    def list_trace_steps(self, conversation_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM execution_steps
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def log_evaluation(self, result: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO evaluations (
                    name, passed, latency_ms, tool_success_rate, answer_score, details_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result["name"],
                    int(result["passed"]),
                    float(result["latency_ms"]),
                    float(result["tool_success_rate"]),
                    float(result["answer_score"]),
                    json.dumps(result.get("details", {}), sort_keys=True),
                    utc_now_iso(),
                ),
            )

    def list_evaluations(self, limit: int = 25) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM evaluations ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
