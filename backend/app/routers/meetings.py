import os
import shutil
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Meeting, Participant, User
from app.schemas import MeetingOut, MeetingListItem
from app.services.transcription import transcribe_audio
from app.services.extraction import extract_structured_data
from app.services.ingestion import download_audio_from_url, get_youtube_transcript
from app.services import rag
from app.auth import get_current_user

router = APIRouter(prefix="/meetings", tags=["meetings"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _run_extraction_and_index(db, meeting: Meeting, transcript: str):
    """Shared final step, regardless of where the transcript came from."""
    meeting.transcript = transcript
    meeting.status = "extracting"
    db.commit()

    result = extract_structured_data(transcript)
    meeting.summary = result["summary"]
    meeting.decisions = result["decisions"]
    meeting.action_items = result["action_items"]
    meeting.open_debates = result["open_debates"]
    meeting.status = "done"
    db.commit()

    try:
        rag.index_meeting(meeting.id, meeting.title, meeting.owner_id, transcript)
    except Exception:
        pass


def process_meeting(meeting_id: str, audio_path: str):
    """Background task for the direct-upload flow: transcribe -> extract -> save."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return

        meeting.status = "transcribing"
        db.commit()
        transcript = transcribe_audio(audio_path)

        _run_extraction_and_index(db, meeting, transcript)
    except Exception as e:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting:
            meeting.status = "failed"
            db.commit()
        raise e
    finally:
        db.close()


def process_meeting_from_url(meeting_id: str, url: str):
    """
    Background task for the link-based flow. Tries YouTube's own captions
    first (near-instant, no download) - falls back to download + Whisper
    transcription only if captions aren't available.
    """
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return

        meeting.status = "downloading"
        db.commit()

        transcript = get_youtube_transcript(url)

        if transcript is None:
            audio_path = download_audio_from_url(url)
            meeting.audio_path = audio_path
            meeting.status = "transcribing"
            db.commit()
            transcript = transcribe_audio(audio_path)

        _run_extraction_and_index(db, meeting, transcript)
    except Exception as e:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting:
            meeting.status = "failed"
            db.commit()
        raise e
    finally:
        db.close()


@router.post("/upload", response_model=MeetingOut)
def upload_meeting(
    background_tasks: BackgroundTasks,
    title: str = Form("Untitled meeting"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".wav"
    saved_path = os.path.join(UPLOAD_DIR, f"{meeting_id}{ext}")

    with open(saved_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    meeting = Meeting(
        id=meeting_id,
        owner_id=current_user.id,
        title=title,
        status="uploaded",
        audio_path=saved_path,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    background_tasks.add_task(process_meeting, meeting_id, saved_path)

    return meeting


class MeetingFromUrl(BaseModel):
    url: str
    title: str = "Untitled meeting"


@router.post("/from-url", response_model=MeetingOut)
def upload_meeting_from_url(
    payload: MeetingFromUrl,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts a YouTube link, a public/shared Google Drive link, or any other
    URL yt-dlp supports. The server downloads the audio directly - the
    file never passes through the browser, so this works for large files
    without hitting upload limits.
    """
    meeting_id = str(uuid.uuid4())

    meeting = Meeting(
        id=meeting_id,
        owner_id=current_user.id,
        title=payload.title,
        status="downloading",
        audio_path=None,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    background_tasks.add_task(process_meeting_from_url, meeting_id, payload.url)

    return meeting


@router.get("", response_model=list[MeetingListItem])
def list_meetings(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    return (
        db.query(Meeting)
        .filter(Meeting.owner_id == current_user.id)
        .order_by(Meeting.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id, Meeting.owner_id == current_user.id)
        .first()
    )
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting