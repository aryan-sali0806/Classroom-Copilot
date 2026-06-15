import logging
import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Assignment, Attachment, Course, PollLog, User
from app.services.classroom_service import get_classroom_service, parse_due_date

logger = logging.getLogger(__name__)


def poll_for_user(user: User, db: Session, triggered_by: str = "scheduler") -> dict:
    start = time.time()
    courses_checked = assignments_found = new_assignments = 0
    error = None

    try:
        service = get_classroom_service(user)
        courses = db.query(Course).filter(Course.user_id == user.id, Course.state == "ACTIVE").all()
        courses_checked = len(courses)

        for course in courses:
            try:
                response = (
                    service.courses()
                    .courseWork()
                    .list(courseId=course.google_course_id, courseWorkStates=["PUBLISHED"])
                    .execute()
                )
                courseworks = response.get("courseWork", [])
                assignments_found += len(courseworks)

                for cw in courseworks:
                    existing = db.query(Assignment).filter(
                        Assignment.google_assignment_id == cw["id"]
                    ).first()

                    if existing:
                        continue

                    assignment = Assignment(
                        google_assignment_id=cw["id"],
                        course_id=course.id,
                        title=cw.get("title", "Untitled"),
                        description=cw.get("description"),
                        due_date=parse_due_date(cw),
                        max_points=int(cw["maxPoints"]) if cw.get("maxPoints") else None,
                        state="new",
                    )
                    db.add(assignment)
                    db.flush()

                    for material in cw.get("materials", []):
                        drive_file = material.get("driveFile", {}).get("driveFile")
                        if drive_file:
                            db.add(Attachment(
                                assignment_id=assignment.id,
                                google_drive_id=drive_file.get("id"),
                                file_name=drive_file.get("title", "attachment"),
                                mime_type=drive_file.get("mimeType"),
                            ))

                    new_assignments += 1

            except Exception as e:
                logger.warning("Failed to poll course %s: %s", course.google_course_id, e)

        db.commit()

    except Exception as e:
        error = str(e)
        logger.error("Poll failed for user %s: %s", user.id, e)
        db.rollback()

    duration_ms = int((time.time() - start) * 1000)
    log = PollLog(
        user_id=user.id,
        triggered_by=triggered_by,
        courses_checked=courses_checked,
        assignments_found=assignments_found,
        new_assignments=new_assignments,
        duration_ms=duration_ms,
        error=error,
    )
    db.add(log)
    db.commit()

    return {
        "courses_checked": courses_checked,
        "assignments_found": assignments_found,
        "new_assignments": new_assignments,
        "duration_ms": duration_ms,
        "error": error,
    }


def start_scheduler(app):
    from apscheduler.schedulers.background import BackgroundScheduler

    from app.core.config import settings
    from app.db.database import SessionLocal

    scheduler = BackgroundScheduler()

    def scheduled_poll():
        db = SessionLocal()
        try:
            users = db.query(User).all()
            for user in users:
                poll_for_user(user, db, triggered_by="scheduler")
        finally:
            db.close()

    scheduler.add_job(
        scheduled_poll,
        "interval",
        minutes=settings.POLL_INTERVAL_MINUTES,
        id="assignment_poller",
    )
    scheduler.start()
    logger.info("Poller started — interval: %d min", settings.POLL_INTERVAL_MINUTES)
    return scheduler
