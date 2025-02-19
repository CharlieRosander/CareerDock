from fastapi import APIRouter
from .endpoints import jobs, auth, pages

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(pages.router, tags=["pages"])  # No prefix for pages
api_router.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
api_router.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
