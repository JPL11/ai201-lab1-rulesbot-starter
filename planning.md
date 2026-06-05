# RulesBot — Planning Doc

Use this file to record your design decisions as you work through the lab.
There are no wrong answers — write enough that you could explain your reasoning to another group.

---

## Chunking Strategy

**Chunk size:**

300 characters (character-based sliding window). Produces 167 chunks across
9 rule books (~19 per book) — long enough to hold one complete rule, short
enough to return targeted results.

**Overlap:**

50 characters. A rule that spans a chunk boundary survives intact in one of
the two neighbors. This matters more than usual here because the window cuts
on raw character count, so many chunks start mid-word ("x, that hex
produces…") — the overlap is what keeps the complete sentence retrievable.

**Why this strategy fits rule book text:**

Rule books are semantically dense: one paragraph = one self-contained rule,
which is exactly the granularity questions arrive at ("what happens when…").
300 chars ≈ 2–3 sentences ≈ one rule. We verified the extremes break it
(see chunking experiment below): 75-char chunks fragment rules into
meaningless slivers; 1,500-char chunks merge unrelated rules so no single
question matches well.

---

## Retrieval Observations

After implementing retrieval, try these test queries and record what comes back:

| Query | Top result game | Does it make sense? |
|-------|----------------|---------------------|
| "How do you win?" | Monopoly (0.507), then Risk, Ticket to Ride | Yes — generic victory question legitimately matches every rulebook; near-identical distances across games confirm it |
| "What happens when you roll a 7?" | Catan (0.466), then Risk ×2 | Yes — top hit is the robber rule; Risk dice chunks at ranks 2–3 are semantically reasonable noise |
| "Can two players share a route?" | Ticket To Ride (0.344) ×3 | Yes — all three from TTR, exactly the double-route rule |

**Anything surprising?**

Absolute distances run much higher than the lab's rule of thumb: clearly
correct matches score 0.29–0.47, never 0.1–0.2. With short chunks and MiniLM
embeddings, only the *relative* ordering means anything — so we return all
k=3 unfiltered rather than tuning a distance threshold, and let the
generation prompt refuse when context doesn't contain the answer. Eval
(`eval.py`, 18 questions, 2 per game): **18/18 top-1, 18/18 top-3**.

---

## Response Quality

After implementing generation, try 2–3 questions and assess the answers:

| Query | Answer accurate? | Properly grounded? | Cited the right game? |
|-------|-----------------|-------------------|----------------------|
| "How do you get out of Jail in Monopoly?" | Yes | Yes — says "three turns" verbatim from docs/monopoly.txt, where common knowledge says "two"; the model is provably reading the doc, not memory | Yes |
| "What are the rules of chess castling?" (before chess.txt existed) | n/a | Yes — refused: "I couldn't find that in the loaded rule books." | n/a |
| "How do you win?" | Yes | Yes — answered per game, and flagged that the Ticket to Ride chunk only covers tiebreakers instead of filling the gap from memory | Yes, all three |

**What would you change about the prompt to improve grounding?**

The clause that earned its place: "even if you are confident you know the
answer." Board game rules are heavily represented in training data, so a
positive instruction ("use the text below") isn't enough — the model needs
its own knowledge explicitly declared off-limits. Next iterations to try:
(1) require a direct quote from the rule text alongside each answer, making
grounding failures self-evident; (2) few-shot the refusal case so the exact
fallback string is more reliable.

---

## Optional Challenges

**Ninth game** — added `docs/chess.txt`, written in the same style as the
existing books (ALL-CAPS sections, complete prose). After re-ingest (167
chunks), retrieval quality matches the pre-loaded games: castling queries hit
at dist 0.299–0.39. Document quality matters — complete, self-contained
sentences embed as well as the originals. Best demo: the exact question
RulesBot refused before ("chess castling") now gets a full cited answer.

**Chunking extremes** (`chunking_experiment.py` — ephemeral collections, real
DB untouched):

| Config | Chunks | "Roll a 7?" result |
|---|---|---|
| small_75 (75/15) | 681 | Top dist *improves* (0.338) but results are unusable: fragments that name rules without containing them, plus wrong-game keyword matches (Monopoly "roll doubles", Uno "Red 7") |
| baseline_300 (300/50) | 167 | Correct: Catan robber rule first, complete passage |
| large_1500 (1500/200) | 35 | Fails: Risk dice chunk wins (0.656); each chunk blends several rules, so the robber paragraph is diluted past recognition |

Key lesson: **lower distance ≠ better retrieval** across chunking configs —
short chunks score better and retrieve worse. The improvement direction isn't
size but boundaries (sentence/section-aware splitting at ~300 chars).

**Eval agent** (`eval.py`) — 18 known question→game pairs run through
`retrieve()`, reporting top-1/top-k accuracy with full failure logs.
Retrieval-only (no LLM calls), so it's free to run after any chunking change:
`rm -rf chroma_db/ && python app.py`, then `python eval.py`, compare scores.
