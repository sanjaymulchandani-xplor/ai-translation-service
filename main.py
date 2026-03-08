from __future__ import annotations

from typing import Optional

import ollama
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from translation_service import Translator
from translation_service.config import MODEL, SUPPORTED_LANGUAGES, SYSTEM_PROMPT

app = FastAPI()
translator = Translator()


class TranslateRequest(BaseModel):
    content: str
    source_language: str
    target_language: str
    context: Optional[str] = None


class TranslateResponse(BaseModel):
    translation: str


class BatchRequest(BaseModel):
    texts: list[str]
    source_language: str
    target_language: str


class BatchResponse(BaseModel):
    translations: list[str]


def _validate_languages(src: str, tgt: str) -> None:
    if src not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source language: '{src}'.",
        )
    if tgt not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported target language: '{tgt}'.",
        )


@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    try:
        result = translator.translate(
            req.content, req.source_language, req.target_language, req.context
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TranslateResponse(translation=result)


@app.post("/translate/batch", response_model=BatchResponse)
def translate_batch(req: BatchRequest):
    try:
        results = translator.translate_batch(
            req.texts, req.source_language, req.target_language
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BatchResponse(translations=results)


@app.post("/translate/stream")
def translate_stream(req: TranslateRequest):
    src = req.source_language.lower()
    tgt = req.target_language.lower()
    _validate_languages(src, tgt)

    def generate():
        stream = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"{src.capitalize()} → {tgt.capitalize()}\n{req.content}",
                },
            ],
            stream=True,
        )
        for chunk in stream:
            yield chunk.message.content

    return StreamingResponse(generate(), media_type="text/plain")
