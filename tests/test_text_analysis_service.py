"""Unit tests for the text-analysis service (pure logic, no MCP involved)."""

from __future__ import annotations

import pytest

from app.services.text_analysis_service import analyze_text


def test_analyze_text_counts_words_and_characters() -> None:
    result = analyze_text("Hello world.")

    assert result.word_count == 2
    assert result.character_count == 12
    assert result.sentence_count == 1


def test_analyze_text_counts_multiple_sentences() -> None:
    result = analyze_text("One. Two! Three?")

    assert result.sentence_count == 3


def test_analyze_text_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="empty"):
        analyze_text("   ")


def test_analyze_text_reading_time_scales_with_word_count() -> None:
    short = analyze_text("word " * 10)
    long = analyze_text("word " * 200)

    assert long.estimated_reading_time_seconds > short.estimated_reading_time_seconds
