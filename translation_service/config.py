from __future__ import annotations

from pathlib import Path

SUPPORTED_LANGUAGES = {"english", "german", "french", "japanese"}

MODEL = "minimax-m2.5:cloud"
EMBEDDING_MODEL = "nomic-embed-text"

SIMILARITY_THRESHOLD = 0.97
MAX_RETRIES = 3
CACHE_MAX_SIZE = 2048

DB_PATH = Path(__file__).parent.parent / "translations.db"

SYSTEM_PROMPT = (
    "You are a SaaS localization engine. "
    "Translate UI text naturally for native speakers. "
    "Preserve placeholders, HTML, and markdown. "
    "Return only the translated text."
)
