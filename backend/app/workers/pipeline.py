import logging

from app.agents import classifier, reviewer, solver
from app.db.models import Assignment, User
from app.services.attachment_service import download_and_extract

logger = logging.getLogger(__name__)


def run_pipeline(assignment_id: int, user_id: int) -> dict:
    """
    Full AI pipeline: AttachmentAgent → ClassifierAgent → SolverAgent → ReviewerAgent.
    Creates its own DB session so it is safe to run as a FastAPI BackgroundTask.
    State transitions: new/failed → processing → solved (or failed).
    """
    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            return {"error": "Assignment not found"}

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}

        assignment.state = "processing"
        db.commit()

        # Step 1 — download & extract attachment text
        for attachment in assignment.attachments:
            if attachment.download_status == "pending":
                download_and_extract(user, attachment, db)
        db.commit()

        # Step 2 — classify assignment type
        assignment_type = classifier.classify(assignment, db)
        db.commit()
        logger.info("Assignment %s classified as: %s", assignment_id, assignment_type)

        # Step 3 — generate solution
        solution = solver.solve(assignment, db)
        db.commit()
        logger.info(
            "Solution created for assignment %s (solution_id=%s)", assignment_id, solution.id
        )

        # Step 4 — self-review
        reviewer.review(assignment, solution, db)

        assignment.state = "solved"
        db.commit()

        return {"status": "solved", "solution_id": solution.id}

    except Exception as e:
        logger.error("Pipeline failed for assignment %s: %s", assignment_id, e, exc_info=True)
        try:
            assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
            if assignment:
                assignment.state = "failed"
                db.commit()
        except Exception:
            pass
        return {"error": str(e)}

    finally:
        db.close()
