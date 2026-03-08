from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from .config import DB_PATH


class TranslationMemory:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or str(DB_PATH)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_text TEXT NOT NULL,
                    source_language TEXT NOT NULL,
                    target_language TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    embedding TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(source_text, source_language, target_language)
                )
            """
            )

    def exact_match(self, text: str, src: str, tgt: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT translated_text FROM translations "
                "WHERE source_text = ? AND source_language = ? AND target_language = ?",
                (text, src, tgt),
            ).fetchone()
        return row[0] if row else None

    def store(
        self,
        text: str,
        src: str,
        tgt: str,
        translation: str,
        embedding: list[float],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO translations "
                "(source_text, source_language, target_language, translated_text, embedding, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    text,
                    src,
                    tgt,
                    translation,
                    json.dumps(embedding),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def get_all_with_embeddings(
        self, src: str, tgt: str
    ) -> list[tuple[str, str, list[float]]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT source_text, translated_text, embedding FROM translations "
                "WHERE source_language = ? AND target_language = ? AND embedding IS NOT NULL",
                (src, tgt),
            ).fetchall()
        return [(r[0], r[1], json.loads(r[2])) for r in rows]
