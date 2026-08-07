"""Pydantic models for the text-analysis tool."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TextAnalysisResult(BaseModel):
    """Summary statistics computed from a piece of text."""

    word_count: int = Field(description="Number of whitespace-separated words.")
    character_count: int = Field(description="Total number of characters, including whitespace.")
    sentence_count: int = Field(description="Number of sentences, split on '.', '!', and '?'.")
    average_word_length: float = Field(description="Mean number of characters per word.")
    estimated_reading_time_seconds: float = Field(
        description="Estimated reading time at 200 words per minute."
    )
