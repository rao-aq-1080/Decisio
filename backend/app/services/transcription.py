"""
Speech-to-text via Groq's free hosted Whisper API — no local model,
no torch, nothing to download. Just an HTTP call.
"""
import os
import httpx

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_WHISPER_MODEL = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")
GROQ_TRANSCRIBE_ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions"


def transcribe_audio(file_path: str) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys "
            "and add it to your .env file."
        )

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "audio/mpeg")}
        data = {"model": GROQ_WHISPER_MODEL, "response_format": "text"}
        with httpx.Client(timeout=180) as client:
            resp = client.post(GROQ_TRANSCRIBE_ENDPOINT, headers=headers, files=files, data=data)
            resp.raise_for_status()

    return resp.text.strip()
