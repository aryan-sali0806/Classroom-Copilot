from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    access_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_enc: Mapped[str] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    courses: Mapped[list["Course"]] = relationship(back_populates="user")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_course_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    section: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    enrollment_code: Mapped[str] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String, default="ACTIVE")
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="courses")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="course")


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_assignment_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    max_points: Mapped[int] = mapped_column(Integer, nullable=True)
    assignment_type: Mapped[str] = mapped_column(
        Enum("essay", "coding", "math", "mcq", "unknown", name="assignment_type_enum"),
        default="unknown",
    )
    state: Mapped[str] = mapped_column(
        Enum(
            "new", "processing", "solved", "approved", "rejected", "submitted", "failed",
            name="assignment_state_enum",
        ),
        default="new",
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    course: Mapped["Course"] = relationship(back_populates="assignments")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="assignment")
    solution: Mapped["Solution"] = relationship(back_populates="assignment", uselist=False)


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), nullable=False)
    google_drive_id: Mapped[str] = mapped_column(String, nullable=True)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=True)
    local_path: Mapped[str] = mapped_column(String, nullable=True)
    download_status: Mapped[str] = mapped_column(
        Enum("pending", "downloaded", "failed", name="download_status_enum"),
        default="pending",
    )
    extracted_text: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    assignment: Mapped["Assignment"] = relationship(back_populates="attachments")


class Solution(Base):
    __tablename__ = "solutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id"), unique=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    content_md: Mapped[str] = mapped_column(Text, nullable=True)
    prompt_used: Mapped[str] = mapped_column(Text, nullable=True)
    model_used: Mapped[str] = mapped_column(String, nullable=True)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=True)
    pdf_path: Mapped[str] = mapped_column(String, nullable=True)
    pdf_generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("draft", "approved", "rejected", name="solution_status_enum"),
        default="draft",
    )
    reviewer_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    assignment: Mapped["Assignment"] = relationship(back_populates="solution")
    versions: Mapped[list["SolutionVersion"]] = relationship(back_populates="solution")
    submission: Mapped["Submission"] = relationship(back_populates="solution", uselist=False)


class SolutionVersion(Base):
    __tablename__ = "solution_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solution_id: Mapped[int] = mapped_column(ForeignKey("solutions.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    edited_by: Mapped[str] = mapped_column(
        Enum("user", "ai", name="edited_by_enum"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    solution: Mapped["Solution"] = relationship(back_populates="versions")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solution_id: Mapped[int] = mapped_column(ForeignKey("solutions.id"), nullable=False)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), nullable=False)
    google_submission_id: Mapped[str] = mapped_column(String, nullable=True)
    drive_file_id: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "uploaded", "failed", name="submission_status_enum"),
        default="pending",
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    solution: Mapped["Solution"] = relationship(back_populates="submission")


class PollLog(Base):
    __tablename__ = "poll_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    triggered_by: Mapped[str] = mapped_column(
        Enum("scheduler", "manual", name="trigger_type_enum"), nullable=False
    )
    courses_checked: Mapped[int] = mapped_column(Integer, default=0)
    assignments_found: Mapped[int] = mapped_column(Integer, default=0)
    new_assignments: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    error: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
