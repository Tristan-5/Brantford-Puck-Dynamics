"""Utility functions for identifying high-risk or high-frequency regions."""

from __future__ import annotations


def top_k_sections(scores: dict[str, float], k: int = 10) -> list[tuple[str, float]]:
    """Return the top-k sections by score."""
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
