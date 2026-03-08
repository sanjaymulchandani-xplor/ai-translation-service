from __future__ import annotations

from typing import Optional

from .config import CACHE_MAX_SIZE


class TranslationCache:
    def __init__(self, max_size: int = CACHE_MAX_SIZE) -> None:
        self._store: dict[str, str] = {}
        self._max_size = max_size

    @staticmethod
    def _key(text: str, src: str, tgt: str) -> str:
        return f"{src}|{tgt}|{text}"

    def get(self, text: str, src: str, tgt: str) -> Optional[str]:
        return self._store.get(self._key(text, src, tgt))

    def put(self, text: str, src: str, tgt: str, translation: str) -> None:
        if len(self._store) >= self._max_size:
            oldest = next(iter(self._store))
            del self._store[oldest]
        self._store[self._key(text, src, tgt)] = translation

    def clear(self) -> None:
        self._store.clear()
