from fastapi import APIRouter

from app.api.v1.routes import assignments, auth, courses, pdfs, solutions, submissions

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(courses.router)
api_router.include_router(assignments.router)
api_router.include_router(solutions.router)
api_router.include_router(submissions.router)
api_router.include_router(pdfs.router)
