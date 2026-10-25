"""
Text embeddings via Hugging Face's free Inference API — no local model,
no torch, no local downloads. Just an HTTP call, same pattern as
llm_client.py (Groq).
"""
import os
import httpx

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_EMBEDDING_MODEL = os.getenv(
    "HF_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
HF_ENDPOINT = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_EMBEDDING_MODEL}"


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Returns one pooled embedding vector per input text."""
    if not HF_API_TOKEN:
        raise RuntimeError(
            "HF_API_TOKEN is not set. Get a free token at "
            "https://huggingface.co/settings/tokens and add it to your .env file."
        )

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": texts, "options": {"wait_for_model": True}}

    with httpx.Client(timeout=60) as client:
        resp = client.post(HF_ENDPOINT, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    # Most sentence-transformers models return pooled vectors directly
    # (list[list[float]]). Some return token-level output
    # (list[list[list[float]]]) — mean-pool defensively if so.
    vectors = []
    for item in data:
        if item and isinstance(item[0], list):
            dim = len(item[0])
            pooled = [sum(tok[d] for tok in item) / len(item) for d in range(dim)]
            vectors.append(pooled)
        else:
            vectors.append(item)
    return vectors
