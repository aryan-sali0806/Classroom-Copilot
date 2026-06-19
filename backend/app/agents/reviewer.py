import logging

from sqlalchemy.orm import Session

from app.db.models import Assignment, Solution
from app.services.gemini_service import generate

logger = logging.getLogger(__name__)

_PROMPT = """\
You are a critical reviewer checking a student's assignment solution.

Assignment: {title}
Type: {assignment_type}
Instructions: {description}

Solution:
{solution}

Provide concise review notes (3-5 bullet points) covering:
• Completeness — does it address all parts of the assignment?
• Accuracy — are facts, code, or calculations correct?
• Clarity — is it well-written and easy to understand?
• Improvements — 1-2 specific things that could be better.

Be brief and direct. Start each bullet with "•".
"""


def review(assignment: Assignment, solution: Solution, db: Session) -> str:
    prompt = _PROMPT.format(
        title=assignment.title or "",
        assignment_type=assignment.assignment_type or "unknown",
        description=assignment.description or "",
        solution=(solution.content_md or "")[:6000],
    )

    try:
        notes, _, _, _ = generate(prompt, use_flash=True)
        solution.reviewer_notes = notes.strip()
    except Exception as e:
        logger.error("Review failed for solution %s: %s", solution.id, e)
        solution.reviewer_notes = "Automated review could not be completed."

    db.add(solution)
    return solution.reviewer_notes or ""
