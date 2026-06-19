import io
import logging
from pathlib import Path

import fitz  # pymupdf
from docx import Document
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decrypt
from app.db.models import Attachment, User

logger = logging.getLogger(__name__)

_STORAGE = Path(settings.STORAGE_PATH) / "attachments"


def _drive_service(user: User):
    credentials = Credentials(
        token=decrypt(user.access_token_enc),
        refresh_token=decrypt(user.refresh_token_enc) if user.refresh_token_enc else None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    return build("drive", "v3", credentials=credentials)


def _extract_text(path: Path, mime_type: str) -> str:
    try:
        if mime_type == "application/pdf" or path.suffix.lower() == ".pdf":
            doc = fitz.open(str(path))
            return "\n".join(page.get_text() for page in doc)
        if (
            mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            or path.suffix.lower() == ".docx"
        ):
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
        # plain text or Google Docs exported as text/plain
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.warning("Text extraction failed for %s: %s", path, e)
        return ""


def download_and_extract(user: User, attachment: Attachment, db: Session) -> str:
    """Download a Drive file, save locally, extract text, and update the DB record."""
    if not attachment.google_drive_id:
        return ""

    _STORAGE.mkdir(parents=True, exist_ok=True)
    drive = _drive_service(user)

    try:
        meta = drive.files().get(
            fileId=attachment.google_drive_id, fields="mimeType,name"
        ).execute()
        remote_mime = meta.get("mimeType", "")

        is_google_doc = remote_mime.startswith("application/vnd.google-apps.")
        if is_google_doc:
            request = drive.files().export_media(
                fileId=attachment.google_drive_id, mimeType="text/plain"
            )
            ext = ".txt"
            effective_mime = "text/plain"
        else:
            request = drive.files().get_media(fileId=attachment.google_drive_id)
            ext = Path(meta.get("name", "file")).suffix or ""
            effective_mime = remote_mime

        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buf.seek(0)

        local_path = _STORAGE / f"{attachment.id}{ext}"
        local_path.write_bytes(buf.read())

        text = _extract_text(local_path, effective_mime)

        attachment.local_path = str(local_path)
        attachment.download_status = "downloaded"
        attachment.extracted_text = text[:50_000]  # cap at 50k chars
        db.add(attachment)

        return text

    except Exception as e:
        logger.error("Download failed for attachment %s: %s", attachment.id, e)
        attachment.download_status = "failed"
        db.add(attachment)
        return ""
