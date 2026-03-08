from __future__ import annotations

from typing import Optional

import numpy as np

from .config import SIMILARITY_THRESHOLD


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


MIN_LENGTH_FOR_SIMILARITY = 8


def find_similar(
    query_text: str,
    query_embedding: list[float],
    stored: list[tuple[str, str, list[float]]],
    threshold: float = SIMILARITY_THRESHOLD,
) -> Optional[tuple[str, str, float]]:
    """Find the most similar stored translation above threshold.

    Returns (source_text, translated_text, score) or None.
    Skips similarity matching for very short texts to avoid false positives.
    """
    if not stored:
        return None

    # Short strings have unreliable embeddings — only use exact match for them
    if len(query_text) < MIN_LENGTH_FOR_SIMILARITY:
        return None

    query = np.array(query_embedding)
    best_score = 0.0
    best_match: Optional[tuple[str, str, float]] = None

    for source_text, translated_text, emb in stored:
        score = cosine_similarity(query, np.array(emb))
        if score > best_score:
            best_score = score
            best_match = (source_text, translated_text, score)

    if best_match and best_score >= threshold:
        return best_match
    return None
