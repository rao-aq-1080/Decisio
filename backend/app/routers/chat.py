from fastapi import APIRouter, Depends

from app.models import User
from app.auth import get_current_user
from app.schemas import ChatRequest, ChatResponse
from app.services.chat import chat as chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat_with_meetings(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    history = [m.model_dump() for m in payload.history]
    result = chat_service(query=payload.query, owner_id=current_user.id, history=history)
    return result
