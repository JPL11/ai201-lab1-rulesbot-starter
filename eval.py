"""
Optional challenge: a small eval agent for retrieval quality.

Instead of manually spot-checking RulesBot's answers, this script runs a fixed
set of questions where the correct source game is known, checks whether that
game appears in the retrieved results, and reports accuracy:

  - top-1 accuracy: the closest chunk comes from the right game
  - top-k accuracy: the right game appears anywhere in the k retrieved chunks
    (k = N_RESULTS from config.py — what generate_response() actually sees)

Failures are logged with their full result lists for human review. This is a
simplified version of how production RAG retrieval is evaluated.

Run: python eval.py
"""

from config import N_RESULTS
from retriever import retrieve

# (question, expected game) — two per rulebook: one using game-specific
# vocabulary, one phrased the way a player would actually ask.
EVAL_SET = [
    ("What happens when you roll a 7?", "Catan"),
    ("Can I build a settlement next to another settlement?", "Catan"),
    ("When is castling legal?", "Chess"),
    ("What happens when a pawn reaches the other side of the board?", "Chess"),
    ("How does making a Suggestion work?", "Clue"),
    ("How do you win Clue?", "Clue"),
    ("How does the Spymaster give clues?", "Codenames"),
    ("What happens if you guess the assassin?", "Codenames"),
    ("How do you get out of Jail in Monopoly?", "Monopoly"),
    ("What happens when you land on Free Parking?", "Monopoly"),
    ("What happens when a city gets a 4th disease cube?", "Pandemic"),
    ("How do you cure a disease?", "Pandemic"),
    ("How many dice does the attacker roll in Risk?", "Risk"),
    ("How do you earn cards for conquering territories?", "Risk"),
    ("Can two players claim the same route in Ticket to Ride?", "Ticket To Ride"),
    ("How do destination tickets score?", "Ticket To Ride"),
    ("When can you play a Wild Draw Four?", "Uno"),
    ("What happens if you forget to say Uno?", "Uno"),
]


def run_eval():
    top1_hits, topk_hits, failures = 0, 0, []

    for question, expected in EVAL_SET:
        results = retrieve(question)
        games = [r["game"] for r in results]

        top1 = bool(games) and games[0] == expected
        topk = expected in games
        top1_hits += top1
        topk_hits += topk
        if not topk:
            failures.append((question, expected, results))

        marker = "✓" if top1 else ("~" if topk else "✗")
        print(f"  {marker} [{expected:>14}] {question}")
        print(f"      retrieved: {games}  (top dist: {results[0]['distance']:.3f})")

    n = len(EVAL_SET)
    print(f"\n{'=' * 60}")
    print(f"top-1 accuracy: {top1_hits}/{n} = {top1_hits / n:.0%}")
    print(f"top-{N_RESULTS} accuracy: {topk_hits}/{n} = {topk_hits / n:.0%}")

    if failures:
        print(f"\n{len(failures)} FAILURE(S) for human review:")
        for question, expected, results in failures:
            print(f"\n  Q: {question}  (expected: {expected})")
            for r in results:
                text = r["text"].replace("\n", " ")[:80]
                print(f"    [{r['game']}] (dist: {r['distance']:.3f}) {text}...")
    else:
        print("\nNo top-k failures.")

    return topk_hits / n


if __name__ == "__main__":
    print(f"Running retrieval eval ({len(EVAL_SET)} questions, k={N_RESULTS})...\n")
    run_eval()
