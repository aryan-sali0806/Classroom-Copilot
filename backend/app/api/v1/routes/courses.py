from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import Course, User
from app.services.classroom_service import get_classroom_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
def list_courses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.user_id == user.id).all()
    return [
        {
            "id": c.id,
            "google_course_id": c.google_course_id,
            "name": c.name,
            "section": c.section,
            "state": c.state,
            "synced_at": c.synced_at,
        }
        for c in courses
    ]


@router.post("/sync")
def sync_courses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = get_classroom_service(user)
    response = service.courses().list(studentId="me", courseStates=["ACTIVE"]).execute()
    google_courses = response.get("courses", [])

    synced, created = 0, 0
    for gc in google_courses:
        course = db.query(Course).filter(Course.google_course_id == gc["id"]).first()
        if course:
            course.name = gc.get("name", course.name)
            course.section = gc.get("section")
            course.description = gc.get("descriptionHeading")
            course.state = gc.get("courseState", "ACTIVE")
            course.synced_at = datetime.utcnow()
            synced += 1
        else:
            course = Course(
                google_course_id=gc["id"],
                user_id=user.id,
                name=gc.get("name", ""),
                section=gc.get("section"),
                description=gc.get("descriptionHeading"),
                enrollment_code=gc.get("enrollmentCode"),
                state=gc.get("courseState", "ACTIVE"),
            )
            db.add(course)
            created += 1

    db.commit()
    return {"synced": synced, "created": created, "total": len(google_courses)}


@router.get("/{course_id}/assignments")
def list_course_assignments(
    course_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(
        Course.id == course_id, Course.user_id == user.id
    ).first()
    if not course:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Course not found")
    return [
        {
            "id": a.id,
            "title": a.title,
            "state": a.state,
            "due_date": a.due_date,
            "assignment_type": a.assignment_type,
        }
        for a in course.assignments
    ]
