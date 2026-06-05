from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)


def generate_response(query, retrieved_chunks):
    """
    Generate a grounded answer from retrieved rule chunks.

    TODO — Milestone 3:

    `retrieved_chunks` is the list returned by retrieve(). Each item is a dict:
      - "text"     : the chunk text
      - "game"     : the game name
      - "distance" : similarity score (you can use this to filter weak matches)

    Before writing code, talk through these with your group:
      - How will you format the chunks into a context block for the prompt?
      - What instructions will stop the model from answering beyond what the
        rules say? (Grounding is the whole point — a confident wrong answer
        is worse than an honest "I don't know.")
      - How will you surface which game each answer comes from?

    Your response should:
      1. Answer using only the retrieved context — not the model's general knowledge
      2. Make clear which game the answer comes from
      3. Say so clearly when the answer isn't in the loaded rules

    Return the response as a plain string.
    """
    if not retrieved_chunks:
        return (
            "I couldn't find anything relevant in the loaded rule books. "
            "Try rephrasing your question — or check that your ingestion pipeline is working."
        )

    # Label each chunk with its source game so the model can cite it.
    context = "\n\n".join(
        f"[Source: {chunk['game']} rulebook]\n{chunk['text']}"
        for chunk in retrieved_chunks
    )

    system_prompt = (
        "You are RulesBot, a board game rules assistant.\n"
        "Answer the user's question using ONLY the rule text provided below the "
        "question. Do not draw on outside knowledge or fill in gaps from what "
        "you know about board games — even if you are confident you know the "
        "answer. If the provided text does not contain the answer, reply "
        "exactly: \"I couldn't find that in the loaded rule books.\" Do not "
        "guess.\n"
        "Always state which game's rulebook your answer comes from, e.g. "
        "\"According to the Catan rules, ...\". If the provided text is only "
        "partially relevant, answer the part you can and say what is missing."
    )

    user_message = f"Question: {query}\n\nRule text:\n{context}"

    completion = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return completion.choices[0].message.content
