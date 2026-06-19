from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import Assignment, User
from app.workers.pipeline import run_pipeline
from app.workers.poller import poll_for_user

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("")
def list_assignments(
    status: str | None = None,
    course_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Assignment)
        .join(Assignment.course)
        .filter(Assignment.course.has(user_id=user.id))
    )
    if status:
        query = query.filter(Assignment.state == status)
    if course_id:
        query = query.filter(Assignment.course_id == course_id)
    assignments = query.order_by(Assignment.first_seen_at.desc()).all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "state": a.state,
            "assignment_type": a.assignment_type,
            "due_date": a.due_date,
            "course_id": a.course_id,
            "first_seen_at": a.first_seen_at,
        }
        for a in assignments
    ]


@router.get("/{assignment_id}")
def get_assignment(
    assignment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assignment = (
        db.query(Assignment)
        .join(Assignment.course)
        .filter(Assignment.id == assignment_id, Assignment.course.has(user_id=user.id))
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "state": assignment.state,
        "assignment_type": assignment.assignment_type,
        "due_date": assignment.due_date,
        "max_points": assignment.max_points,
        "course_id": assignment.course_id,
        "attachments": [
            {"id": att.id, "file_name": att.file_name, "mime_type": att.mime_type}
            for att in assignment.attachments
        ],
    }


@router.post("/{assignment_id}/pipeline", status_code=202)
def trigger_pipeline(
    assignment_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assignment = (
        db.query(Assignment)
        .join(Assignment.course)
        .filter(Assignment.id == assignment_id, Assignment.course.has(user_id=user.id))
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if assignment.state == "processing":
        raise HTTPException(status_code=409, detail="Pipeline already running for this assignment")

    background_tasks.add_task(run_pipeline, assignment_id, user.id)
    return {"status": "pipeline started", "assignment_id": assignment_id}


@router.post("/poll")
def manual_poll(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = poll_for_user(user, db, triggered_by="manual")
    return result
