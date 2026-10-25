"""
Meeting understanding via Groq's free hosted API (open-source models,
OpenAI-compatible). See llm_client.py for the shared client.

We force strict JSON output so the backend can parse it without regex.
"""
import json

from app.services.llm_client import chat_completion

SYSTEM_PROMPT = """You are a meeting analyst. You will be given a raw meeting \
transcript. Extract structured information from it.

Respond with ONLY valid JSON, no markdown fences, no commentary, matching \
exactly this schema:

{
  "summary": "one paragraph executive summary",
  "decisions": [{"decision": "string", "made_by": "string or Unknown"}],
  "action_items": [{"task": "string", "owner": "string or Unassigned", "deadline": "string or Not specified"}],
  "open_debates": [{"topic": "string", "positions": ["string", "string"]}]
}

Rules:
- If a field has nothing to report, use an empty list [].
- Never invent names, owners, or deadlines that aren't implied by the transcript.
- Keep the summary factual and concise.
"""


def extract_structured_data(transcript: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Transcript:\n\n{transcript}"},
    ]

    raw_content = chat_completion(messages, json_mode=True)

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        # Fallback: strip accidental markdown fences and retry once
        cleaned = raw_content.strip().strip("`").replace("json\n", "", 1)
        parsed = json.loads(cleaned)

    return {
        "summary": parsed.get("summary", ""),
        "decisions": parsed.get("decisions", []),
        "action_items": parsed.get("action_items", []),
        "open_debates": parsed.get("open_debates", []),
    }
