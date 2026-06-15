from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import settings
from app.core.security import decrypt
from app.db.models import User


def get_classroom_service(user: User):
    credentials = Credentials(
        token=decrypt(user.access_token_enc),
        refresh_token=decrypt(user.refresh_token_enc) if user.refresh_token_enc else None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    return build("classroom", "v1", credentials=credentials)


def parse_due_date(coursework: dict) -> datetime | None:
    due = coursework.get("dueDate")
    due_time = coursework.get("dueTime")
    if not due:
        return None
    return datetime(
        year=due["year"],
        month=due["month"],
        day=due["day"],
        hour=due_time.get("hours", 0) if due_time else 0,
        minute=due_time.get("minutes", 0) if due_time else 0,
    )
