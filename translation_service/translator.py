from __future__ import annotations

import time
from typing import Optional

import ollama

from .cache import TranslationCache
from .config import MAX_RETRIES, MODEL, SUPPORTED_LANGUAGES, SYSTEM_PROMPT
from .embedding_service import get_embedding
from .translation_memory import TranslationMemory
from .vector_store import find_similar


class Translator:
    def __init__(self) -> None:
        self.memory = TranslationMemory()
        self.cache = TranslationCache()

    @staticmethod
    def _validate_language(lang: str) -> str:
        lang = lang.lower()
        if lang not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: '{lang}'. "
                "Supported: English, German, French, Japanese."
            )
        return lang

    def _call_llm(
        self, text: str, src: str, tgt: str, context: str | None = None
    ) -> str:
        user_content = f"{src.capitalize()} → {tgt.capitalize()}\n{text}"
        if context:
            user_content = f"Context: {context}\n{user_content}"

        for attempt in range(MAX_RETRIES):
            try:
                response = ollama.chat(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                )
                return response.message.content
            except Exception:
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(2**attempt)

    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: str | None = None,
    ) -> str:
        src = self._validate_language(source_language)
        tgt = self._validate_language(target_language)

        # 1. In-memory cache
        cached = self.cache.get(text, src, tgt)
        if cached is not None:
            return cached

        # 2. Exact match in translation memory (SQLite)
        exact = self.memory.exact_match(text, src, tgt)
        if exact is not None:
            self.cache.put(text, src, tgt, exact)
            return exact

        # 3. Vector similarity search
        embedding = get_embedding(text)
        stored = self.memory.get_all_with_embeddings(src, tgt)
        similar = find_similar(text, embedding, stored)
        if similar is not None:
            _, translation, _ = similar
            self.memory.store(text, src, tgt, translation, embedding)
            self.cache.put(text, src, tgt, translation)
            return translation

        # 4. Call LLM (only when no match found)
        translation = self._call_llm(text, src, tgt, context)

        # 5. Store result for future reuse
        self.memory.store(text, src, tgt, translation, embedding)
        self.cache.put(text, src, tgt, translation)

        return translation

    def translate_batch(
        self,
        texts: list[str],
        source_language: str,
        target_language: str,
    ) -> list[str]:
        src = self._validate_language(source_language)
        tgt = self._validate_language(target_language)

        # Deduplicate while preserving order
        unique = list(dict.fromkeys(texts))
        results: dict[str, str] = {}
        need_embedding: list[str] = []

        # Phase 1: Check cache and exact matches
        for text in unique:
            cached = self.cache.get(text, src, tgt)
            if cached is not None:
                results[text] = cached
                continue

            exact = self.memory.exact_match(text, src, tgt)
            if exact is not None:
                results[text] = exact
                self.cache.put(text, src, tgt, exact)
                continue

            need_embedding.append(text)

        # Phase 2: Vector similarity for remaining
        need_llm: list[tuple[str, list[float]]] = []
        if need_embedding:
            stored = self.memory.get_all_with_embeddings(src, tgt)
            for text in need_embedding:
                embedding = get_embedding(text)
                similar = find_similar(text, embedding, stored)
                if similar is not None:
                    _, translation, _ = similar
                    results[text] = translation
                    self.memory.store(text, src, tgt, translation, embedding)
                    self.cache.put(text, src, tgt, translation)
                else:
                    need_llm.append((text, embedding))

        # Phase 3: LLM only for truly new translations
        for text, embedding in need_llm:
            translation = self._call_llm(text, src, tgt)
            results[text] = translation
            self.memory.store(text, src, tgt, translation, embedding)
            self.cache.put(text, src, tgt, translation)

        return [results[text] for text in texts]
