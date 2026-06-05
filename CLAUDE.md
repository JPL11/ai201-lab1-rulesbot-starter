# RulesBot — Claude Instructions

## What this is

AI201 Lab 1: a starter repo for **RulesBot**, a board game rules assistant built on a RAG (Retrieval-Augmented Generation) pipeline. The UI (Gradio) and infrastructure (ChromaDB + sentence-transformers + Groq LLM) are wired up. The student fills in three milestones.

This is a **learning exercise**. The point is for the student to think through and implement the RAG pipeline themselves. When asked for help, prefer Socratic hints and pointing at the relevant spec — don't drop a finished implementation unless explicitly asked.

## Tech stack

- **Python 3** + `venv`
- **Gradio 5.20** — chat UI (`app.py`)
- **ChromaDB 1.5** — persistent vector store at `./chroma_db`
- **sentence-transformers 3.4** with `all-MiniLM-L6-v2` embeddings (~80MB, downloaded on first run)
- **Groq** SDK with `llama-3.3-70b-versatile` for generation
- **python-dotenv** for `GROQ_API_KEY` from `.env`

All knobs live in `config.py` (model names, `N_RESULTS=3`, paths). Change values there, not inline.

## Pipeline

```
docs/*.txt  →  ingest.load_documents()  →  ingest.chunk_document()
            →  retriever.embed_and_store()  →  ChromaDB (./chroma_db)

user query  →  retriever.retrieve()  →  generator.generate_response()  →  UI
```

## Milestones (what's TODO)

| Milestone | File | Function | Status |
|---|---|---|---|
| 1 | `ingest.py` | `chunk_document()` | ✅ Implemented (300-char sliding window, 50 overlap, 50 min) — read and understand before milestone 2 |
| 2 | `retriever.py` | `retrieve()` | ❌ TODO — use `_collection.query()`, return `[{text, game, distance}]` |
| 3 | `generator.py` | `generate_response()` | ❌ TODO — Groq chat completion grounded in retrieved chunks |

Each milestone has a paired spec in `specs/` that the student is expected to complete *before* writing code. Always direct attention to the spec first.

Reflections go in `planning.md` (chunking strategy, retrieval observations, response quality).

## Common commands

```bash
# One-time setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add GROQ_API_KEY

# Run the app
python app.py

# Re-ingest after changing chunking
rm -rf chroma_db/
python app.py
```

## Important gotchas

- **ChromaDB persists.** Ingestion is skipped on startup if `_collection.count() > 0`. After editing `chunk_document()` (or chunking params in `config.py`), delete `./chroma_db/` or the new strategy won't take effect.
- **`_collection.query()` returns nested lists** — one entry per query. With a single query, index `[0]` to flatten.
- **Distance is cosine** (per `metadata={"hnsw:space": "cosine"}` in `retriever.py`) — lower = more similar. Don't invert it.
- **Grounding is the assignment's whole point.** When helping with `generate_response()`, the system prompt must keep the model from answering beyond the retrieved chunks. A confident wrong answer is worse than "I don't know."
- **Never commit `.env`** — it's gitignored, keep it that way.
- **Free Groq tier** has rate limits; expect occasional 429s during heavy testing.

## Where to start when asked for help

1. Point at `specs/system-design.md` if context is unclear.
2. Point at the milestone-specific spec before writing code.
3. Only then look at the `.py` file. Hint, don't hand over solutions.
