# Spec: `generate_response()`

**File:** `generator.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user query and a list of retrieved rule chunks, generate a response that directly answers the question using only the retrieved text as context. The response must be grounded — it should not draw on the model's general knowledge of board games, only on what was retrieved.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's original question |
| `retrieved_chunks` | `list[dict]` | Ranked list of chunks from `retrieve()`, each with `"text"`, `"game"`, and `"distance"` |

**Output:** `str`

A plain string containing the response to show the user. The response should:
- Answer the question using only the retrieved rule text
- Identify which game the answer comes from
- Acknowledge clearly when the answer is not found in the loaded rules

Returns a fallback string (not an error) when `retrieved_chunks` is empty.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Context formatting

*How will you format the retrieved chunks before passing them to the LLM? Describe the structure — not the code. Consider: will you label chunks by game? Include distance scores? Separate chunks with delimiters?*

```
Each chunk is prefixed with a source label on its own line —
"[Source: <Game> rulebook]" — followed by the raw chunk text, with chunks
separated by blank lines. The label is what lets the model attribute its
answer to the right game (and is required for the citation instruction to
work). Distance scores are NOT included: they're meaningless to the model
and risk it hedging ("this result is only loosely relevant...").
```

---

### System prompt — grounding instruction

*Write the exact system prompt instruction you will use to prevent the model from answering beyond the retrieved text. This is the most important design decision in this function.*

```
Answer the user's question using ONLY the rule text provided below the
question. Do not draw on outside knowledge or fill in gaps from what you know
about board games — even if you are confident you know the answer. If the
provided text does not contain the answer, reply exactly: "I couldn't find
that in the loaded rule books." Do not guess.
```

---

### System prompt — citation instruction

*Write the exact instruction you will use to tell the model to identify which game its answer comes from.*

```
Always state which game's rulebook your answer comes from, e.g. "According to
the Catan rules, ...". If the provided text is only partially relevant, answer
the part you can and say what is missing.
```

---

### Fallback behavior

*What should the response say when the answer isn't found in the loaded rule books? Write the exact fallback message.*

```
Two distinct fallbacks:
1. retrieved_chunks is empty (handled in code, no API call):
   "I couldn't find anything relevant in the loaded rule books. Try rephrasing
   your question — or check that your ingestion pipeline is working."
2. Chunks were retrieved but don't contain the answer (handled by the prompt):
   "I couldn't find that in the loaded rule books."
```

---

### Handling low-relevance chunks

*`retrieved_chunks` may include chunks with high distance scores (weak relevance). Will you filter these out before building context, pass them all in, or handle them another way? What are the tradeoffs?*

```
Pass all chunks in and rely on the grounding instruction to refuse when the
text doesn't answer the question. With only k=3 short chunks the noise risk
is small, and a distance cutoff is hard to tune (correct matches in this
corpus already score 0.37–0.47). Tradeoff: an irrelevant chunk in context
could distract the model toward the wrong game — if that shows up in testing,
add a filter here (e.g. drop chunks with distance > 0.7) rather than in
retrieve(), so the search function stays a pure ranking.
```

---

### Message structure

*Describe how you will structure the messages list for the API call — what goes in the system message vs. the user message?*

```
Two messages:
- system: the standing behavior rules — RulesBot persona, grounding
  instruction, exact-refusal fallback, citation instruction. Nothing
  query-specific lives here.
- user: "Question: <query>" followed by "Rule text:" and the formatted,
  source-labeled chunks. Putting the context in the user message (after the
  question) keeps the system prompt stable across calls and makes it
  unambiguous that "the rule text provided below the question" refers to
  this turn's retrieved chunks.
```

---

## Implementation Notes

*Fill this in after implementing and testing.*

**Test query and response:**

```
Query: How do you get out of Jail in Monopoly?
Response: "According to the Monopoly rules, to get out of Jail, you can: pay a
$50 fine before rolling on any of your next three turns, use a Get Out of Jail
Free card, or roll doubles on any of your three turns in Jail. ..."
Correctly grounded? Yes — the answer says "three turns", matching docs/monopoly.txt
verbatim, where common Monopoly knowledge (and the lab handout) says "two
turns". The model demonstrably answered from the document, not training data.
Cited the right game? Yes ("According to the Monopoly rules").
Grounding probe: "What are the rules of chess castling?" → "I couldn't find
that in the loaded rule books." — refuses correctly for out-of-corpus questions.
```

**One thing you changed from your original spec after seeing the actual output:**

```
Added the "even if you are confident you know the answer" clause to the
grounding instruction — board game rules are heavily represented in training
data, so the model needs an explicit instruction that its own knowledge is
off-limits, not just a positive "use the text below" framing.
```
