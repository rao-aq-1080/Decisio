"""
Shared LLM client — calls Groq's free hosted API (OpenAI-compatible),
which serves open-source models (Llama 3.x, etc.) on Groq's own hardware.

Used instead of a local Ollama model to avoid running a 4B+ parameter
model on-device, which is heavy on 8GB RAM machines. Whisper and the
embedding/reranker models still run locally — this is the one piece
that got moved to a free hosted API for memory reasons.
"""
import os
import httpx

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


def chat_completion(messages: list[dict], json_mode: bool = False) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys "
            "and add it to your .env file."
        )

    payload = {"model": GROQ_MODEL, "messages": messages}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    with httpx.Client(timeout=60) as client:
        resp = client.post(GROQ_ENDPOINT, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"]
