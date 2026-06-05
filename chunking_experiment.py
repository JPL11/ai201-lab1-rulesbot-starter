"""
Optional challenge: break the chunking strategy on purpose.

Builds two ephemeral (in-memory) ChromaDB collections from the same rule
documents — one with extremely small chunks (75 chars) and one with extremely
large chunks (1,500 chars) — then runs the same queries against both, plus the
real 300-char collection, and prints the results side by side.

The persistent ./chroma_db store is never touched. Observations are written up
in planning.md.

Run: python chunking_experiment.py
"""

import chromadb
from chromadb.utils import embedding_functions

from config import EMBEDDING_MODEL
from ingest import load_documents, chunk_document
from retriever import retrieve  # the real 300-char collection

CONFIGS = {
    "small_75": {"chunk_size": 75, "overlap": 15, "min_length": 20},
    "large_1500": {"chunk_size": 1500, "overlap": 200, "min_length": 50},
}

QUERIES = [
    "What happens when you roll a 7?",
    "How do you get out of Jail in Monopoly?",
    "When is castling legal in Chess?",
]


def build_collection(client, ef, name, docs, params):
    collection = client.create_collection(
        name=name, embedding_function=ef, metadata={"hnsw:space": "cosine"}
    )
    chunks = [c for d in docs for c in chunk_document(d["text"], d["game"], **params)]
    collection.add(
        documents=[c["text"] for c in chunks],
        metadatas=[{"game": c["game"]} for c in chunks],
        ids=[c["chunk_id"] for c in chunks],
    )
    print(f"  {name}: {len(chunks)} chunks")
    return collection


def query_collection(collection, query, n_results=3):
    r = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"text": t, "game": m["game"], "distance": d}
        for t, m, d in zip(r["documents"][0], r["metadatas"][0], r["distances"][0])
    ]


def show(label, results, preview=90):
    print(f"  --- {label} ---")
    for c in results:
        text = c["text"].replace("\n", " ")[:preview]
        print(f"  [{c['game']}] (dist: {c['distance']:.3f}) {text}...")


if __name__ == "__main__":
    print("Building ephemeral collections...")
    docs = load_documents()
    client = chromadb.EphemeralClient()
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    collections = {
        name: build_collection(client, ef, name, docs, params)
        for name, params in CONFIGS.items()
    }

    for query in QUERIES:
        print(f"\n{'=' * 70}\nQ: {query}\n")
        show("baseline_300 (real collection)", retrieve(query))
        for name, collection in collections.items():
            show(name, query_collection(collection, query))
