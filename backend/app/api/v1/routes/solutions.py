from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import Assignment, Course, Solution, User

router = APIRouter(prefix="/solutions", tags=["solutions"])


@router.get("/{solution_id}")
def get_solution(
    solution_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    solution = (
        db.query(Solution)
        .join(Solution.assignment)
        .join(Assignment.course)
        .filter(Solution.id == solution_id, Course.user_id == user.id)
        .first()
    )
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")
    return {
        "id": solution.id,
        "assignment_id": solution.assignment_id,
        "version": solution.version,
        "content_md": solution.content_md,
        "model_used": solution.model_used,
        "tokens_in": solution.tokens_in,
        "tokens_out": solution.tokens_out,
        "status": solution.status,
        "reviewer_notes": solution.reviewer_notes,
        "created_at": solution.created_at,
        "updated_at": solution.updated_at,
    }


@router.get("/by-assignment/{assignment_id}")
def get_solution_by_assignment(
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
    if not assignment.solution:
        raise HTTPException(status_code=404, detail="No solution yet for this assignment")

    s = assignment.solution
    return {
        "id": s.id,
        "assignment_id": s.assignment_id,
        "version": s.version,
        "content_md": s.content_md,
        "model_used": s.model_used,
        "tokens_in": s.tokens_in,
        "tokens_out": s.tokens_out,
        "status": s.status,
        "reviewer_notes": s.reviewer_notes,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }
