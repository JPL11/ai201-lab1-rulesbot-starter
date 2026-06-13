# 🎲 RulesBot

> A board game rules assistant — because "just read the rulebook" isn't always helpful at 11pm on game night.

RulesBot answers natural-language questions about board game rules using a RAG (Retrieval-Augmented Generation) pipeline: it retrieves the most relevant rule passages from a vector store and generates an answer grounded strictly in that retrieved text.

**Status: complete.** All three milestones are implemented, the retrieval evaluation suite passes 18/18, and both optional challenges (ninth rulebook, chunking-extremes experiment) are done. Built for AI201 Lab 1.

---

## How It Works

```
docs/*.txt ─→ load_documents() ─→ chunk_document() ─→ embed_and_store() ─→ ChromaDB
                                                                              │
user query ─→ retrieve() ─→ top-k chunks ─→ generate_response() ─→ grounded answer
```

| Stage | File | Implementation |
|---|---|---|
| **Chunking** | `ingest.py` | 300-character sliding window with 50-character overlap; fragments under 50 characters are dropped. Overlap prevents rules from being split mid-sentence across chunk boundaries. |
| **Embedding & storage** | `retriever.py` | `all-MiniLM-L6-v2` sentence-transformer embeddings stored in a persistent ChromaDB collection (cosine distance), tagged with the source game. |
| **Retrieval** | `retriever.py` | Semantic top-k search (`N_RESULTS = 3`), returning `{text, game, distance}` per hit. Typical distances for on-topic queries land around 0.29–0.47 (cosine — lower is more similar). |
| **Generation** | `generator.py` | Groq `llama-3.3-70b-versatile` chat completion. The system prompt restricts the model to the retrieved chunks and instructs it to say it doesn't know rather than guess — a confident wrong ruling is worse than no ruling. |

### Tech stack

Python 3 · Gradio 5.20 (chat UI) · ChromaDB 1.5 (persistent vector store) · sentence-transformers 3.4 (`all-MiniLM-L6-v2`) · Groq SDK (`llama-3.3-70b-versatile`) · python-dotenv

All tunables (model names, chunk parameters, `N_RESULTS`, paths) live in `config.py`.

---

## Evaluation & Experiments

- **`eval.py`** — retrieval evaluation suite: 18 known question→passage pairs across the rulebooks. The implemented pipeline retrieves the correct passage for **18/18** queries.
- **`chunking_experiment.py`** — optional challenge: sweeps chunk size to the extremes and compares retrieval quality. Finding: bigger chunks are not better — oversized chunks dilute the embedding and drag in off-topic text, while undersized ones strip context. The 300/50 middle ground won on both retrieval distance and answer quality.
- **Ninth rulebook** — optional challenge: added `docs/chess.txt` and re-ingested to confirm the pipeline generalizes to a new game with zero code changes.
- **`planning.md`** — design reflections: chunking-strategy rationale, retrieval observations (distance ranges, failure modes), and response-quality notes.

---

## Getting Started

### 1. Clone and create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
# or: .venv\Scripts\activate   # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `sentence-transformers` downloads the embedding model (~80MB) on first run. It's cached locally afterward.

### 3. Add your Groq API key

```bash
cp .env.example .env
```

Open `.env` and replace `your_key_here` with your key from [console.groq.com](https://console.groq.com). No credit card required. (The free tier is rate-limited — expect occasional 429s under heavy testing.)

### 4. Run the app

```bash
python app.py
```

First launch ingests all rulebooks into `./chroma_db` (skipped on later launches since the collection persists), then opens the chat UI in your browser.

### Re-ingesting after chunking changes

ChromaDB persists to disk, so a changed chunking strategy won't take effect until you delete the store:

```bash
rm -rf chroma_db/   # Mac/Linux
# or: rmdir /s chroma_db   # Windows
python app.py
```

---

## Project Structure

```
rulesbot/
├── app.py                   # Gradio UI and startup/ingestion logic
├── config.py                # All tunables: models, paths, chunk + retrieval params
├── ingest.py                # Document loading + sliding-window chunking
├── retriever.py             # ChromaDB store, embedding, semantic retrieval
├── generator.py             # Grounded Groq chat completion
├── eval.py                  # Retrieval evaluation suite (18 known pairs)
├── chunking_experiment.py   # Chunk-size extremes experiment
├── planning.md              # Design reflections and observations
├── docs/                    # Rulebooks (9 games)
└── specs/                   # Design docs — completed before each milestone
    ├── system-design.md
    ├── chunk-document-spec.md
    ├── retrieve-spec.md
    └── generate-response-spec.md
```

## Rule Books Included

| Game | File |
|------|------|
| Catan | `docs/catan.txt` |
| Chess | `docs/chess.txt` |
| Clue | `docs/clue.txt` |
| Codenames | `docs/codenames.txt` |
| Monopoly | `docs/monopoly.txt` |
| Pandemic | `docs/pandemic.txt` |
| Risk | `docs/risk.txt` |
| Ticket to Ride | `docs/ticket_to_ride.txt` |
| Uno | `docs/uno.txt` |
