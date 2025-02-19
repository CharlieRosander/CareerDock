from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.services.job_service import JobService
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def root(request: Request):
    """Landing page"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Dashboard page with overview and statistics"""
    try:
        job_service = JobService(db)
        jobs = job_service.get_user_jobs(current_user.id)

        # TODO: Calculate statistics for the dashboard
        active_applications = len([j for j in jobs if j.status == "Applied"])
        interviews_scheduled = len([j for j in jobs if j.status == "Interview"])
        follow_ups_due = len([j for j in jobs if j.status == "Follow Up"])

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user,
                "active_applications": active_applications,
                "interviews_scheduled": interviews_scheduled,
                "follow_ups_due": follow_ups_due,
                "recent_jobs": jobs[:5],  # Show 5 most recent jobs
            },
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail="Database error occurred while fetching dashboard data",
        )


@router.get("/job-registry")
async def job_registry(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Job registry page

    This page shows all jobs for the current user and allows them to manage their applications.
    """
    try:
        job_service = JobService(db)
        jobs = job_service.get_user_jobs(current_user.id)

        return templates.TemplateResponse(
            "job_registry.html",
            {"request": request, "user": current_user, "jobs": jobs},
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, detail="Database error occurred while fetching jobs"
        )
