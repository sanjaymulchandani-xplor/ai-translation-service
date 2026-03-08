# AI Translation Service

A SaaS UI translation service that translates text between English, German, French, and Japanese using Ollama with the MiniMax M2.5 model.

The system uses translation memory and vector similarity to reduce LLM calls by reusing previous translations.

## How It Works

1. Check in-memory cache for an exact match
2. Check SQLite translation memory for an exact match
3. Check vector similarity (cosine similarity >= 0.97) against stored translations
4. Call the LLM only if no match is found
5. Store the result for future reuse

## Requirements

- Python 3.9+
- Ollama running locally
- Models: `minimax-m2.5:cloud` and `nomic-embed-text`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn numpy ollama
ollama pull nomic-embed-text
```

## Run

```bash
.venv/bin/uvicorn main:app --reload --port 8787
```

## API

### POST /translate

Translate a single string.

```json
{
  "content": "Save changes",
  "source_language": "English",
  "target_language": "French"
}
```

### POST /translate/batch

Translate multiple strings with deduplication.

```json
{
  "texts": ["Save", "Cancel", "Delete"],
  "source_language": "English",
  "target_language": "German"
}
```

### POST /translate/stream

Stream the translation response as plain text.

## Supported Languages

- English
- German
- French
- Japanese
