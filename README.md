# Decisio 🎙️

AI that turns any meeting recording into decisions, action items, owners,
deadlines, and unresolved debates — genuinely lightweight: no local ML
models, no torch, nothing heavy to download. Everything that needs real
compute runs on free hosted APIs.

## Stack — everything heavy is a hosted free API
- **Frontend:** Next.js
- **Backend:** FastAPI
- **Auth:** JWT (python-jose + bcrypt) — self-contained, no external service
- **Database:** SQLite (native setup) or PostgreSQL (Docker setup)
- **Transcription:** Groq's free hosted Whisper API — no local model
- **Meeting understanding & chat:** Groq's free hosted LLM API — no local model
- **Embeddings (search/chat):** Hugging Face's free Inference API — no local model
- **Vector storage:** Qdrant Cloud free tier — fully hosted
- **Link ingestion:** yt-dlp (runs locally, but it's lightweight — just downloads audio)

Your machine's job in this stack: run FastAPI, run SQLite, make HTTP
calls to the four free services above. No multi-gigabyte model
downloads, no torch, no GPU/compute-heavy local inference.

## Before you start: three free accounts
1. **Groq** — console.groq.com/keys — powers transcription, extraction, and chat
2. **Hugging Face** — huggingface.co/settings/tokens — powers embeddings for search/chat
3. **Qdrant Cloud** — cloud.qdrant.io — free cluster for vector storage

Keep all three keys somewhere safe — paste them into your local `.env`
file only, never into chat, code comments, or anywhere else.

---

## Running WITHOUT Docker (recommended — this is now genuinely light)

### 1. Install
- **Python 3.11** — https://www.python.org/downloads/release/python-3119/
  (check "Add to PATH"). Use 3.11 specifically for the most mature wheel support.
- **Node.js 18+** — https://nodejs.org
- **FFmpeg** — `winget install --id Gyan.FFmpeg -e`, then close/reopen
  your terminal. Only needed for the link-ingestion feature (yt-dlp uses
  it to extract audio from video); file uploads don't need it.

### 2. Set up the backend
```powershell
cd decisio\backend
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.native.example .env
```
Open `backend\.env` and fill in your real `GROQ_API_KEY`, `HF_API_TOKEN`,
`QDRANT_HOST`, `QDRANT_API_KEY`, and a random `JWT_SECRET`.

Run it:
```powershell
uvicorn app.main:app --reload --port 8000
```
Startup should be near-instant now — there are no local models to load.

### 3. Set up the frontend (new terminal)
```powershell
cd decisio\frontend
npm install
npm run dev
```

### 4. Open http://localhost:3000
Register, upload a file or paste a link, and watch it process.

---

## Running WITH Docker

```bash
docker compose up -d --build
```
Starts PostgreSQL, Mailpit, and the FastAPI backend. Fill in `.env` with
the same four values as above, then:
```bash
cd frontend
npm install
npm run dev
```

## Useful URLs
- Frontend: http://localhost:3000
- Backend docs (Swagger): http://localhost:8000/docs
- Mailpit inbox (Docker only): http://localhost:8025

## Project layout

```
decisio/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt          # lightweight — no torch, no local ML models
│   ├── requirements-postgres.txt # adds psycopg2-binary, for Docker only
│   ├── .env.native.example
│   └── app/
│       ├── main.py            # FastAPI entrypoint — no model preloading needed
│       ├── database.py        # SQLAlchemy (SQLite or Postgres)
│       ├── models.py          # User, Meeting, Participant (DB-agnostic)
│       ├── schemas.py
│       ├── auth.py            # bcrypt + JWT
│       ├── routers/
│       │   ├── auth.py
│       │   ├── meetings.py    # upload / from-url / list / get
│       │   ├── search.py
│       │   └── chat.py
│       └── services/
│           ├── transcription.py    # Groq hosted Whisper API
│           ├── llm_client.py       # shared Groq LLM client
│           ├── extraction.py       # structured extraction, uses llm_client
│           ├── embeddings_client.py # Hugging Face hosted embeddings
│           ├── rag.py              # chunk + embed + index + search (Qdrant Cloud)
│           ├── chat.py             # RAG-grounded chat, uses llm_client + rag.py
│           └── ingestion.py        # yt-dlp: downloads audio from links
└── frontend/                       # Next.js app (dashboard, chat, meeting pages)
```

## Roadmap (not yet built)
- Celery + Redis → async processing queue instead of FastAPI BackgroundTasks
- Keycloak → real multi-org authentication
- MinIO → object storage for audio files instead of local disk
- Prometheus + Grafana → ops monitoring
- WhatsApp/email auto-dispatch of action items
- `DELETE /meetings/{id}` that also calls `rag.delete_meeting_chunks()`

## Notes
- Free API tiers (Groq, Hugging Face, Qdrant Cloud) all have rate limits
  that can change — check each provider's dashboard if you hit errors.
- Large audio files may hit size limits on Groq's free Whisper endpoint —
  check console.groq.com for current limits if a big file fails.
- Removing reranking (vs. an earlier version of this project) trades a
  little search precision for a much simpler, lighter stack. Worth
  revisiting only if search results feel consistently off.
