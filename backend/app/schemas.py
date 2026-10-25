from typing import Optional, List
from pydantic import BaseModel


class ParticipantIn(BaseModel):
    name: str
    email: Optional[str] = None


class MeetingOut(BaseModel):
    id: str
    title: str
    status: str
    transcript: Optional[str] = None
    summary: Optional[str] = None
    decisions: Optional[list] = None
    action_items: Optional[list] = None
    open_debates: Optional[list] = None

    class Config:
        from_attributes = True


class MeetingListItem(BaseModel):
    id: str
    title: str
    status: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    query: str
    history: List[ChatMessage] = []


class ChatSource(BaseModel):
    meeting_id: str
    title: str
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource]
