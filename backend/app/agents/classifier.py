import logging

from sqlalchemy.orm import Session

from app.db.models import Assignment
from app.services.gemini_service import generate

logger = logging.getLogger(__name__)

_VALID = {"essay", "coding", "math", "mcq", "unknown"}

_PROMPT = """\
You are classifying a school assignment into one of five categories.

Assignment title: {title}
Assignment description: {description}
Attachment text excerpt (up to 2000 chars):
{excerpt}

Respond with EXACTLY ONE word from this list: essay, coding, math, mcq, unknown
Do not include any other text.
"""


def classify(assignment: Assignment, db: Session) -> str:
    attachment_text = "".join(
        (att.extracted_text or "") + "\n" for att in assignment.attachments
    )

    prompt = _PROMPT.format(
        title=assignment.title or "",
        description=assignment.description or "",
        excerpt=attachment_text[:2000],
    )

    try:
        text, _, _, _ = generate(prompt, use_flash=True)
        category = text.strip().lower().split()[0] if text.strip() else "unknown"
        if category not in _VALID:
            category = "unknown"
    except Exception as e:
        logger.error("Classification failed for assignment %s: %s", assignment.id, e)
        category = "unknown"

    assignment.assignment_type = category
    db.add(assignment)
    return category
