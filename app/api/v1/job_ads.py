from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.job_ad import JobAdBase, JobAdCreate, JobAdUpdate
from app.services.job_registry_service import create_job_ad as create_job_ad_service

router = APIRouter()


@router.post("/create_job_ad", response_model=JobAdCreate)
async def create_job_ad(
    request: Request,
    job_ad: JobAdCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new job advertisement
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_job_ad_service(db=db, job_ad=job_ad)


@router.put("/update_job_ad/{job_ad_id}", response_model=JobAdUpdate)
async def update_job_ad(
    request: Request,
    job_ad_id: int, 
    job_ad: JobAdUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing job advertisement
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    pass


@router.delete("/delete_job_ad/{job_ad_id}")
async def delete_job_ad(
    request: Request,
    job_ad_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a job advertisement
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    pass


@router.get("/get_job_ad/{job_ad_id}", response_model=JobAdBase)
async def get_job_ad(
    request: Request,
    job_ad_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific job advertisement
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    pass


@router.get("/get_all_job_ads", response_model=List[JobAdBase])
async def get_all_job_ads(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all job advertisements
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    pass


@router.post("/create_form")
async def create_job_ad_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Handle job advertisement form submission with HTMX
    """
    if current_user is None:
        return HTMLResponse(content="""
        <div class="alert alert-danger">
            You must be logged in to create a job advertisement.
        </div>
        """, status_code=401)
    
    # Get form data
    form_data = await request.form()
    
    # Create job ad
    try:
        job_ad = JobAdCreate(
            title=form_data.get("title"),
            company=form_data.get("company"),
            location=form_data.get("location"),
            description=form_data.get("description"),
            requirements=form_data.get("requirements"),
            salary_range=form_data.get("salary_range"),
            contact_email=form_data.get("contact_email"),
            contact_phone=form_data.get("contact_phone"),
            application_url=form_data.get("application_url"),
            application_deadline=form_data.get("application_deadline"),
        )
        
        create_job_ad_service(db=db, job_ad=job_ad)
        
        return HTMLResponse(content="""
        <div class="alert alert-success">
            Job advertisement created successfully!
        </div>
        """, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"""
        <div class="alert alert-danger">
            Error creating job advertisement: {str(e)}
        </div>
        """, status_code=400)
