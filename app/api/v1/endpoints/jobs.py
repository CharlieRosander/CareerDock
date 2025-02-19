from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.database import get_db
from app.schemas.job import JobCreate, JobUpdate, Job
from app.services.job_service import JobService
from app.core.auth.dependencies import get_current_user
from app.models.auth import AuthUser
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# HTMX endpoints
@router.get("/new", response_class=HTMLResponse)
async def new_job_form(request: Request):
    """Returnera HTML-formulär för att skapa nytt jobb"""
    return templates.TemplateResponse(
        "components/job_form.html",
        {"request": request}
    )

@router.get("/{job_id}/edit", response_class=HTMLResponse)
async def edit_job_form(
    request: Request,
    job_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Returnera HTML-formulär för att redigera jobb"""
    job_service = JobService(db)
    job = job_service.get_job(job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return templates.TemplateResponse(
        "components/job_form.html",
        {"request": request, "job": job}
    )

@router.get("/search", response_class=HTMLResponse)
async def search_jobs(
    request: Request,
    query: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Sök efter jobb och returnera uppdaterad jobb-lista"""
    job_service = JobService(db)
    jobs = job_service.search_jobs(current_user.id, query)
    return templates.TemplateResponse(
        "components/job_list.html",
        {"request": request, "jobs": jobs}
    )

@router.get("/filter", response_class=HTMLResponse)
async def filter_jobs(
    request: Request,
    status: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Filtrera jobb efter status och returnera uppdaterad jobb-lista"""
    job_service = JobService(db)
    jobs = job_service.filter_jobs(current_user.id, status)
    return templates.TemplateResponse(
        "components/job_list.html",
        {"request": request, "jobs": jobs}
    )

@router.get("/", response_class=HTMLResponse)
async def list_jobs(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Lista alla jobb för användaren"""
    job_service = JobService(db)
    jobs = job_service.get_user_jobs(current_user.id)
    return templates.TemplateResponse(
        "components/job_list.html",
        {"request": request, "jobs": jobs}
    )

@router.post("/", response_class=HTMLResponse)
async def create_job(
    request: Request,
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Skapa nytt jobb och returnera uppdaterad jobb-lista"""
    job_service = JobService(db)
    job = job_service.create_job(current_user.id, job_data)
    jobs = job_service.get_user_jobs(current_user.id)
    return templates.TemplateResponse(
        "components/job_list.html",
        {"request": request, "jobs": jobs}
    )

@router.put("/{job_id}", response_class=HTMLResponse)
async def update_job(
    request: Request,
    job_id: int,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Uppdatera jobb och returnera uppdaterad jobb-lista"""
    job_service = JobService(db)
    job = job_service.update_job(job_id, current_user.id, job_data)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    jobs = job_service.get_user_jobs(current_user.id)
    return templates.TemplateResponse(
        "components/job_list.html",
        {"request": request, "jobs": jobs}
    )

@router.delete("/{job_id}", response_class=HTMLResponse)
async def delete_job(
    request: Request,
    job_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Ta bort jobb och returnera uppdaterad jobb-lista"""
    job_service = JobService(db)
    success = job_service.delete_job(job_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    jobs = job_service.get_user_jobs(current_user.id)
    return templates.TemplateResponse(
        "components/job_list.html",
        {"request": request, "jobs": jobs}
    )

# REST API endpoints
@router.get("/api/v1/jobs", response_model=List[Job])
async def get_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Get all jobs for current user"""
    return JobService(db).get_user_jobs(current_user.id, skip, limit)


@router.post("/api/v1/jobs", response_model=Job, status_code=201)
async def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Create a new job"""
    return JobService(db).create_job(current_user.id, job)


@router.get("/api/v1/jobs/{job_id}", response_model=Job)
async def get_job(
    job_id: int, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)
):
    """Get a specific job"""
    job = JobService(db).get_job(job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/api/v1/jobs/{job_id}", response_model=Job)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Update a job"""
    job = JobService(db).get_job(job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobService(db).update_job(job_id, job_update)


@router.delete("/api/v1/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: int, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)
):
    """Delete a job"""
    job = JobService(db).get_job(job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    JobService(db).delete_job(job_id)
