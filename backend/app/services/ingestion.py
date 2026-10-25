"""
Downloads audio from a URL (YouTube, public Google Drive shared links, or
any other site yt-dlp supports) so the user never has to upload large
files through the browser - the server fetches it directly.

For YouTube specifically, get_youtube_transcript() tries to fetch
YouTube's own auto-generated captions first - near-instant, no download,
no transcription needed at all. download_audio_from_url() is only used
as a fallback when no captions are available, or for non-YouTube links.

Free, open-source, no API key.
"""
import os
import re
import uuid
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

DOWNLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def extract_youtube_id(url: str) -> str | None:
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/embed/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_youtube_transcript(url: str) -> str | None:
    """
    Tries to fetch YouTube's own captions directly - no download, no
    transcription, just an API call. Returns None if the URL isn't
    YouTube or the video has no captions available, so the caller can
    fall back to download_audio_from_url() + Whisper.
    """
    video_id = extract_youtube_id(url)
    if not video_id:
        return None

    try:
        segments = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception:
        return None

    lines = [f"[{seg['start']:.1f}s] {seg['text']}" for seg in segments]
    return "\n".join(lines)


def download_audio_from_url(url: str) -> str:
    """
    Downloads the best available audio track from a URL and converts it to
    mp3. Returns the local file path. Raises an exception with a readable
    message if the URL isn't something yt-dlp can handle (e.g. a private
    or authenticated link).
    """
    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    final_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp3")
    if not os.path.exists(final_path):
        raise RuntimeError(
            "Could not extract audio from this URL. It may require login, "
            "be private, or not be supported."
        )
    return final_path