import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base

# Using plain String(36) for IDs and generic JSON instead of Postgres-only
# UUID/JSONB types, so this works identically on SQLite (native/no-Docker
# setup) and Postgres (Docker setup) without changing any application code.


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    meetings = relationship("Meeting", back_populates="owner", cascade="all, delete-orphan")


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False, default="Untitled meeting")
    status = Column(String, nullable=False, default="uploaded")
    # uploaded/downloading -> transcribing -> extracting -> done -> failed

    audio_path = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)

    summary = Column(Text, nullable=True)
    decisions = Column(JSON, nullable=True)       # list[{decision, made_by}]
    action_items = Column(JSON, nullable=True)    # list[{task, owner, deadline}]
    open_debates = Column(JSON, nullable=True)    # list[{topic, positions}]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    participants = relationship("Participant", back_populates="meeting", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="meetings")


class Participant(Base):
    __tablename__ = "participants"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    meeting_id = Column(String(36), ForeignKey("meetings.id"))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)

    meeting = relationship("Meeting", back_populates="participants")
