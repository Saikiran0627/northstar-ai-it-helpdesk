"""Lightweight safety controls for the local help desk demo."""

from __future__ import annotations

import re
from dataclasses import dataclass


INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bignore (all )?(previous|prior|above) instructions\b",
        r"\breveal (the )?(system|developer) (prompt|message|instructions)\b",
        r"\bprint (the )?(api key|secret|token|environment variables)\b",
        r"\bexfiltrate\b",
        r"\bdisregard (your|the) policies\b",
        r"\byou are now\b",
    ]
]


@dataclass(frozen=True)
class SafetyAssessment:
    allowed: bool
    warning: str | None = None


def assess_user_message(message: str) -> SafetyAssessment:
    for pattern in INJECTION_PATTERNS:
        if pattern.search(message):
            return SafetyAssessment(
                allowed=False,
                warning=(
                    "I can help with IT support, but I cannot follow instructions "
                    "to reveal prompts, secrets, or bypass safety controls."
                ),
            )
    return SafetyAssessment(allowed=True)


def sanitize_document_text(text: str) -> str:
    """Remove document text that looks like instructions to the assistant."""
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        if any(pattern.search(line) for pattern in INJECTION_PATTERNS):
            cleaned_lines.append("[Removed unsafe instruction-like content from source document.]")
        else:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)
