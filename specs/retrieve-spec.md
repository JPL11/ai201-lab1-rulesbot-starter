# Spec: `retrieve()`

**File:** `retriever.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user's natural language query, find the most relevant chunks from the vector store using semantic similarity search. Return them ranked by relevance so that `generate_response()` can use them as context.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's natural language question |
| `n_results` | `int` | Maximum number of chunks to return (default: `N_RESULTS` from `config.py`) |

**Output:** `list[dict]`

Each dict in the returned list must contain exactly these keys:

| Key | Type | Description |
|-----|------|-------------|
| `"text"` | `str` | The chunk text |
| `"game"` | `str` | The game name this chunk came from |
| `"distance"` | `float` | Cosine distance score — lower means more similar to the query |

Results should be ordered from most to least relevant (lowest to highest distance). Returns an empty list `[]` if the collection contains no documents.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Query approach

*Describe how you will use `_collection.query()` to find relevant chunks. What arguments will you pass, and why?*

```
Call _collection.query() with:
- query_texts=[query] — the API takes a list so it can batch multiple queries;
  we wrap our single query string in a list.
- n_results=n_results — how many nearest chunks to return (default N_RESULTS=3
  from config.py).
- include=["documents", "metadatas", "distances"] — we need the chunk text,
  the game name (stored in metadata at ingest time), and the cosine distance.
ChromaDB embeds the query with the same sentence-transformers model used at
ingest, so query and chunks live in the same vector space.
```

---

### Return structure

*Sketch out what one item in your return list looks like as a concrete example. Where does each field come from in the query results?*

```
{
  "text": "iately if: the outbreak marker reaches 8, any color of disease cubes r...",   # results["documents"][0][i]
  "game": "Pandemic",                                                                  # results["metadatas"][0][i]["game"]
  "distance": 0.373,                                                                   # results["distances"][0][i]
}
The three inner lists are parallel (same length, same order), so zip() walks
them together. ChromaDB already returns them sorted by ascending distance, so
no re-sorting is needed.
```

---

### Handling the nested result structure

*`_collection.query()` returns nested lists. Describe what index you need to access to get the actual list of results for a single query, and why the nesting exists.*

```
query() accepts a LIST of query strings and returns one inner list per query —
results["documents"] is list[list[str]], outer index = which query, inner
index = which result. We pass exactly one query, so the outer list always has
one element and results["documents"][0] / ["metadatas"][0] / ["distances"][0]
give the actual result lists. Forgetting the [0] is the classic bug here.
```

---

### Relevance threshold

*Will you filter out results above a certain distance score, or return all `n_results` regardless of how relevant they are? What are the tradeoffs of each approach?*

```
Return all n_results unfiltered, and let the generation step's grounding
prompt handle weak matches ("if the answer is not in the text, say so").
Tradeoff: a hard threshold (e.g. drop distance > 0.7) keeps junk out of the
LLM context, but with 300-char chunks even good matches score ~0.4–0.5 here
(our best "roll a 7" hit was 0.466), so a threshold tuned too tight would
starve the generator of correct context. Filtering at generation time keeps
retrieve() a pure search function and the threshold decision observable.
```

---

### Edge cases

*How does your implementation behave when: (a) the collection is empty, (b) the query matches no chunks well, (c) the query matches chunks from multiple games?*

```
(a) Empty collection: the count() == 0 guard returns [] before querying, and
    generate_response() shows its fallback message.
(b) No good matches: ChromaDB still returns the n_results nearest chunks —
    just with high distances. We pass them through; the grounding prompt in
    generation refuses to answer when the text doesn't contain the answer.
(c) Multiple games: this is correct behavior, not a bug — "how do you win?"
    legitimately matches every rulebook. The game name travels with each chunk
    so the generator can attribute (or disambiguate) per source.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**Test query and top result returned:**

```
Query: What happens when you run out of disease cubes in Pandemic?
Top result game: Pandemic
Distance score: 0.373
Does it make sense? Yes — all three results came from Pandemic, and the top
chunk is the loss-conditions passage ("...any color of disease cubes runs
out..."), which directly answers the question.
```

**One thing about the query results that surprised you:**

```
Even clearly correct matches score ~0.37–0.47, nowhere near the 0.1–0.2
"highly relevant" band from the lab notes — with 300-char chunks of a
MiniLM embedding, absolute cosine distances run high and only the RELATIVE
ordering is meaningful. Also, chunks often start mid-word ("x, that hex
produces...") because the sliding window cuts on character count, not
sentence boundaries.
```
