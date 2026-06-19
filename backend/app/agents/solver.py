import logging

from sqlalchemy.orm import Session

from app.db.models import Assignment, Solution, SolutionVersion
from app.services.gemini_service import generate

logger = logging.getLogger(__name__)

_PROMPTS: dict[str, str] = {
    "essay": """\
You are a skilled student writing a high-quality essay for a school assignment.

Assignment: {title}
Instructions: {description}
Reference material:
{context}

Write a well-structured, comprehensive essay with a clear introduction, body, and conclusion.
Format your response in Markdown.
""",
    "coding": """\
You are an expert programmer completing a coding assignment.

Assignment: {title}
Instructions: {description}
Context:
{context}

Provide a complete, correct solution with:
1. All code in fenced code blocks with the appropriate language tag
2. A brief explanation of your approach
3. Any assumptions you made

Format your response in Markdown.
""",
    "math": """\
You are a mathematics tutor solving a problem step by step.

Assignment: {title}
Problem: {description}
Context:
{context}

Show ALL working steps clearly. State the final answer explicitly.
Use LaTeX notation for equations (e.g. $x^2 + y^2 = z^2$).
Format your response in Markdown.
""",
    "mcq": """\
You are answering multiple choice questions for a school assignment.

Assignment: {title}
Questions: {description}
Context:
{context}

For each question: state which option you choose, explain why it is correct,
and briefly explain why the other identifiable options are incorrect.
Format your response in Markdown.
""",
    "unknown": """\
You are a student completing a school assignment.

Assignment: {title}
Instructions: {description}
Context:
{context}

Provide a thorough, well-organized response that addresses all parts of the assignment.
Format your response in Markdown.
""",
}


def solve(assignment: Assignment, db: Session) -> Solution:
    attachment_text = "".join(
        (att.extracted_text or "") + "\n" for att in assignment.attachments
    )

    template = _PROMPTS.get(assignment.assignment_type or "unknown", _PROMPTS["unknown"])
    prompt = template.format(
        title=assignment.title or "",
        description=assignment.description or "",
        context=attachment_text[:8000],
    )

    text, model_name, tokens_in, tokens_out = generate(prompt, use_flash=False)

    existing = assignment.solution
    if existing:
        existing.version += 1
        existing.content_md = text
        existing.prompt_used = prompt
        existing.model_used = model_name
        existing.tokens_in = tokens_in
        existing.tokens_out = tokens_out
        existing.status = "draft"
        db.add(existing)
        solution = existing
    else:
        solution = Solution(
            assignment_id=assignment.id,
            version=1,
            content_md=text,
            prompt_used=prompt,
            model_used=model_name,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            status="draft",
        )
        db.add(solution)
        db.flush()

    db.add(
        SolutionVersion(
            solution_id=solution.id,
            version=solution.version,
            content_md=text,
            edited_by="ai",
        )
    )

    return solution
