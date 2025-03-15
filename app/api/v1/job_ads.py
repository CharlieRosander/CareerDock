from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.job_ad import JobAdBase, JobAdCreate, JobAdUpdate
from app.services.job_registry_service import (
    create_job_ad as create_job_ad_service,
    get_job_ad as get_job_ad_service,
    get_all_job_ads as get_all_job_ads_service,
    update_job_ad as update_job_ad_service,
    delete_job_ad as delete_job_ad_service,
    search_job_ads as search_job_ads_service,
)
from uuid import UUID

router = APIRouter()


@router.post("/create_job_ad", response_model=JobAdCreate)
async def create_job_ad(
    request: Request,
    job_ad: JobAdCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    job_ad_id: UUID,
    job_ad: JobAdUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    updated_job_ad = update_job_ad_service(
        db=db, job_ad_id=job_ad_id, job_ad_update=job_ad
    )
    if not updated_job_ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job advertisement with id {job_ad_id} not found",
        )
    return updated_job_ad


@router.delete("/delete_job_ad/{job_ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_ad(
    request: Request,
    job_ad_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    deleted = delete_job_ad_service(db=db, job_ad_id=job_ad_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job advertisement with id {job_ad_id} not found",
        )
    return {"status": "success", "message": "Job advertisement deleted successfully"}


@router.get("/get_job_ad/{job_ad_id}", response_model=JobAdBase)
async def get_job_ad(
    request: Request,
    job_ad_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    job_ad = get_job_ad_service(db=db, job_ad_id=job_ad_id)
    if not job_ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job advertisement with id {job_ad_id} not found",
        )
    return job_ad


@router.get("/get_all_job_ads", response_model=List[JobAdBase])
async def get_all_job_ads(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    return get_all_job_ads_service(db=db, skip=skip, limit=limit)


@router.get("/get_job_ads_html", response_class=HTMLResponse)
async def get_job_ads_html(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all job advertisements as HTML for HTMX
    """
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    
    if current_user is None:
        return HTMLResponse(
            content="""
            <div class="alert alert-danger">
                Du måste vara inloggad för att se jobbannonser.
            </div>
            """,
            status_code=401,
        )

    job_ads = get_all_job_ads_service(db=db, skip=skip, limit=limit)
    
    # Render a partial template for the job listings
    return templates.TemplateResponse(
        "partials/job_listings.html",
        {"request": request, "job_ads": job_ads}
    )


@router.get("/search_job_ads", response_model=List[JobAdBase])
async def search_job_ads(
    request: Request,
    search_term: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search for job advertisements
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return search_job_ads_service(
        db=db, search_term=search_term, skip=skip, limit=limit
    )


@router.get("/search_job_ads_html", response_class=HTMLResponse)
async def search_job_ads_html(
    request: Request,
    search_term: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search for job advertisements and return HTML for HTMX
    """
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    
    if current_user is None:
        return HTMLResponse(
            content="""
            <div class="alert alert-danger">
                Du måste vara inloggad för att söka efter jobbannonser.
            </div>
            """,
            status_code=401,
        )

    job_ads = search_job_ads_service(
        db=db, search_term=search_term, skip=skip, limit=limit
    )
    
    # Render a partial template for the search results
    return templates.TemplateResponse(
        "partials/search_results.html",
        {"request": request, "job_ads": job_ads, "search_term": search_term}
    )


@router.post("/create_form")
async def create_job_ad_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Handle job advertisement form submission with HTMX
    """
    if current_user is None:
        return HTMLResponse(
            content="""
        <div class="alert alert-danger">
            You must be logged in to create a job advertisement.
        </div>
        """,
            status_code=401,
        )

    # Get form data
    form_data = await request.form()

    # Create job ad
    try:
        job_ad = JobAdCreate(
            title=form_data.get("title"),
            company=form_data.get("company", ""),
            location=form_data.get("location"),
            description=form_data.get("description", ""),
            job_url=form_data.get("job_url", ""),
            category=form_data.get("category", ""),
        )

        create_job_ad_service(db=db, job_ad=job_ad)

        return HTMLResponse(
            content="""
        <div class="alert alert-success">
            Job advertisement created successfully!
        </div>
        """,
            status_code=200,
        )
    except Exception as e:
        return HTMLResponse(
            content=f"""
        <div class="alert alert-danger">
            Error creating job advertisement: {str(e)}
        </div>
        """,
            status_code=400,
        )
