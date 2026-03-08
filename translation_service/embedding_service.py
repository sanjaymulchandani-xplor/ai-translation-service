from __future__ import annotations

import ollama

from .config import EMBEDDING_MODEL


def get_embedding(text: str) -> list[float]:
    response = ollama.embed(model=EMBEDDING_MODEL, input=text)
    return response.embeddings[0]
