from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import meetings, auth, search, chat

app = FastAPI(title="Decisio API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(meetings.router)
app.include_router(search.router)
app.include_router(chat.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    # No local models to preload anymore — transcription, extraction, chat,
    # and embeddings are all hosted API calls now, so startup is instant.


@app.get("/health")
def health():
    return {"status": "ok"}
