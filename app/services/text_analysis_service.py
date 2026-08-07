"""Pure text-analysis logic, independent of the MCP transport.

Kept free of any FastMCP import so it stays trivially unit-testable and
reusable outside a tool context.
"""

from __future__ import annotations

import re

from app.models.text_analysis import TextAnalysisResult

_SENTENCE_BOUNDARY = re.compile(r"[.!?]+")
_WORDS_PER_MINUTE = 200.0


def analyze_text(text: str) -> TextAnalysisResult:
    """Compute word/character/sentence counts and an estimated reading time.

    Raises:
        ValueError: If `text` is empty or only whitespace.
    """
    if not text.strip():
        raise ValueError("text must not be empty")

    words = text.split()
    word_count = len(words)
    sentence_count = max(1, len([s for s in _SENTENCE_BOUNDARY.split(text) if s.strip()]))
    average_word_length = sum(len(w) for w in words) / word_count if words else 0.0

    return TextAnalysisResult(
        word_count=word_count,
        character_count=len(text),
        sentence_count=sentence_count,
        average_word_length=round(average_word_length, 2),
        estimated_reading_time_seconds=round((word_count / _WORDS_PER_MINUTE) * 60, 1),
    )
