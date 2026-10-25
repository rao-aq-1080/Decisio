"""
Conversational interface over the user's meetings, built on top of the
existing RAG search (services/rag.py). Each turn retrieves fresh context
based on the latest question, so follow-ups work naturally.

Uses the shared Groq-based client (llm_client.py) — same model as
extraction.py.
"""
from app.services import rag
from app.services.llm_client import chat_completion

SYSTEM_PROMPT = """You are Decisio's meeting assistant. You answer questions \
using ONLY the meeting excerpts provided below as context. If the answer \
isn't in the provided excerpts, say you don't have that information in \
the user's meetings — never make something up.

When you reference something, mention which meeting it came from.
Keep answers concise and direct."""


def chat(query: str, owner_id: str, history: list[dict] | None = None) -> dict:
    """
    history: list of {"role": "user"|"assistant", "content": str}, oldest first.
    Returns {"answer": str, "sources": [{"meeting_id", "title", "text"}]}
    """
    history = history or []

    # Retrieve fresh context for the latest question every turn — this is
    # what makes follow-ups work ("what about the deadline?" still finds
    # the right meeting because we re-search each time).
    matches = rag.search_meetings(query=query, owner_id=owner_id, final_k=4)

    if matches:
        context_block = "\n\n".join(
            f"[Meeting: {m['title']}]\n{m['text']}" for m in matches
        )
    else:
        context_block = "(No relevant meeting excerpts found for this question.)"

    messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\nContext:\n{context_block}"}]
    messages.extend(history[-6:])  # keep last few turns to bound prompt size
    messages.append({"role": "user", "content": query})

    answer = chat_completion(messages)

    return {
        "answer": answer,
        "sources": [{"meeting_id": m["meeting_id"], "title": m["title"], "text": m["text"]} for m in matches],
    }
