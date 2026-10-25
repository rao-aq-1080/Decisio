"""
RAG (retrieval-augmented search) over meeting transcripts.

Everything here is hosted/free-API based — no local ML models, no torch.
Embeddings via Hugging Face's free Inference API, vector storage via
Qdrant Cloud's free tier. The backend's local footprint is just plain
Python + HTTP calls.
"""
import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from app.services.embeddings_client import embed_texts

QDRANT_HOST = os.getenv("QDRANT_HOST", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "meeting_chunks"
CHUNK_SIZE = 3   # lines per chunk
CHUNK_OVERLAP = 1

_client: QdrantClient | None = None
_vector_size: int | None = None


def get_qdrant() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)
        _ensure_collection(_client)
    return _client


def _ensure_collection(client: QdrantClient):
    global _vector_size
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        if _vector_size is None:
            _vector_size = len(embed_texts(["dimension probe"])[0])
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=_vector_size, distance=Distance.COSINE),
        )


def chunk_transcript(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    chunks = []
    i = 0
    while i < len(lines):
        chunks.append(" ".join(lines[i:i + chunk_size]))
        i += max(chunk_size - overlap, 1)
    return chunks


def index_meeting(meeting_id: str, title: str, owner_id: str, transcript: str):
    """Called after a meeting finishes transcribing — embeds and stores its chunks."""
    if not transcript:
        return

    client = get_qdrant()
    chunks = chunk_transcript(transcript)
    if not chunks:
        return

    vectors = embed_texts(chunks)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vectors[i],
            payload={
                "meeting_id": meeting_id,
                "owner_id": owner_id,
                "title": title,
                "text": chunks[i],
            },
        )
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)


def delete_meeting_chunks(meeting_id: str):
    """Call this if a meeting is ever deleted, to keep the index clean."""
    client = get_qdrant()
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector={"filter": {"must": [{"key": "meeting_id", "match": {"value": meeting_id}}]}},
    )


def search_meetings(query: str, owner_id: str, final_k: int = 3, **_ignored) -> list[dict]:
    """
    Semantic search scoped to one user's meetings. No reranking step —
    plain vector similarity, kept simple and lightweight.
    """
    client = get_qdrant()
    query_vec = embed_texts([query])[0]

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vec,
        query_filter={"must": [{"key": "owner_id", "match": {"value": owner_id}}]},
        limit=final_k,
    )

    return [
        {
            "meeting_id": c.payload["meeting_id"],
            "title": c.payload["title"],
            "text": c.payload["text"],
            "score": c.score,
        }
        for c in response.points
    ]
