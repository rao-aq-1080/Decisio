from fastapi import APIRouter, Depends, Query
from app.models import User
from app.auth import get_current_user
from app.services import rag

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search_meetings(
    q: str = Query(..., min_length=1, description="Natural language search query"),
    current_user: User = Depends(get_current_user),
):
    results = rag.search_meetings(query=q, owner_id=current_user.id)
    return {"query": q, "results": results}
