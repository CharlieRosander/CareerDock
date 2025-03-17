from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
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
    process_job_form_data,
    get_job_listings,
)
from uuid import UUID


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# Helper functions to reduce code duplication
def auth_required_json(current_user: Optional[User]) -> None:
    """Check if user is authenticated and raise HTTPException if not"""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


def auth_required_html(
    request: Request,
    current_user: Optional[User],
    message: str = "You must be logged in.",
) -> Optional[HTMLResponse]:
    """Check if user is authenticated and return HTML error response if not"""
    if current_user is None:
        return templates.TemplateResponse(
            "partials/alerts.html",
            {"request": request, "alert_type": "danger", "message": message},
            status_code=401,
        )
    return None


def create_alert_response(
    request: Request,
    alert_type: str,
    message: str,
    status_code: int = 200,
    include_refresh: bool = False,
    target_element: str = None,
    refresh_url: str = None,
) -> HTMLResponse:
    """Create an HTML alert response"""
    context = {"request": request, "alert_type": alert_type, "message": message}

    if include_refresh:
        context["include_refresh_script"] = True
        context["target_element"] = target_element
        context["refresh_url"] = refresh_url

    return templates.TemplateResponse(
        "partials/alerts.html", context, status_code=status_code
    )


# Regular API endpoints (JSON responses)
@router.post("/create_job_ad", response_model=JobAdCreate)
async def create_job_ad(
    request: Request,
    job_ad: JobAdCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new job advertisement"""
    auth_required_json(current_user)
    return create_job_ad_service(db=db, job_ad=job_ad)


@router.put("/update_job_ad/{job_ad_id}", response_model=JobAdUpdate)
async def update_job_ad(
    request: Request,
    job_ad_id: UUID,
    job_ad: JobAdUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing job advertisement"""
    auth_required_json(current_user)

    updated_job_ad = update_job_ad_service(
        db=db, job_ad_id=job_ad_id, job_ad_update=job_ad
    )
    if not updated_job_ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job advertisement with id {job_ad_id} not found",
        )
    return updated_job_ad


@router.get("/get_job_ad/{job_ad_id}", response_model=JobAdBase)
async def get_job_ad(
    request: Request,
    job_ad_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific job advertisement"""
    auth_required_json(current_user)

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
    """Get all job advertisements"""
    auth_required_json(current_user)
    return get_all_job_ads_service(db=db, skip=skip, limit=limit)


@router.get("/search_job_ads", response_model=List[JobAdBase])
async def search_job_ads(
    request: Request,
    search_term: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search for job advertisements"""
    auth_required_json(current_user)
    return search_job_ads_service(
        db=db, search_term=search_term, skip=skip, limit=limit
    )


# HTMX endpoints (HTML responses)
@router.delete("/delete_job_ad/{job_ad_id}", response_class=HTMLResponse)
async def delete_job_ad(
    request: Request,
    job_ad_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a job advertisement"""
    auth_response = auth_required_html(
        request, current_user, "You must be logged in to delete job advertisements."
    )
    if auth_response:
        return auth_response

    deleted = delete_job_ad_service(db=db, job_ad_id=job_ad_id)
    if not deleted:
        return create_alert_response(
            request,
            "danger",
            f"Job advertisement with ID {job_ad_id} was not found.",
            status_code=404,
        )

    # Return success message with HTMX triggers to refresh job listings
    return templates.TemplateResponse(
        "partials/alerts.html",
        {
            "request": request,
            "alert_type": "success",
            "message": "Job advertisement successfully deleted!",
            "include_refresh_script": True,
            "target_element": "job-listings",
            "refresh_url": "/api/v1/job_ads/get_job_listings_html",
        },
    )


@router.get("/get_job_listings_html", response_class=HTMLResponse)
async def get_job_listings_html(
    request: Request,
    search_term: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get job advertisements as HTML for HTMX, with optional search"""
    auth_response = auth_required_html(
        request, current_user, "You must be logged in to view job advertisements."
    )
    if auth_response:
        return auth_response

    # Get job ads from database using the service function
    job_ads = get_job_listings(db=db, search_term=search_term, skip=skip, limit=limit)

    # Render a partial template for the job listings
    return templates.TemplateResponse(
        "partials/job_listings.html", {"request": request, "job_ads": job_ads}
    )


@router.get("/get_job_ad_create_form", response_class=HTMLResponse)
async def get_job_ad_create_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the form for creating a new job advertisement"""
    auth_response = auth_required_html(
        request, current_user, "You must be logged in to create job advertisements."
    )
    if auth_response:
        return auth_response

    # Return the empty form for creating a new job ad
    return templates.TemplateResponse(
        "partials/edit_job_modal.html",
        {
            "request": request,
            "job": None,
            "form_action": "/api/v1/job_ads/submit_job_ad_form",
        },
    )


@router.post("/submit_job_ad_form", response_class=HTMLResponse)
async def submit_job_ad_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Handle job advertisement form submission with HTMX"""
    auth_response = auth_required_html(
        request, current_user, "You must be logged in to create job advertisements."
    )
    if auth_response:
        return auth_response

    # Process form data
    try:
        form_data = await request.form()
        job_ad_data = process_job_form_data(form_data)
        job_ad = JobAdCreate(**job_ad_data)

        # Create job ad in database
        create_job_ad_service(db=db, job_ad=job_ad)

        # Return success message with HTMX triggers to close modal and refresh job listings
        return templates.TemplateResponse(
            "partials/alerts.html",
            {
                "request": request,
                "alert_type": "success",
                "message": "Job advertisement created successfully!",
                "include_refresh_script": True,
                "target_element": "job-listings",
                "refresh_url": "/api/v1/job_ads/get_job_listings_html",
            },
        )
    except Exception as e:
        # Return error message
        return create_alert_response(
            request, "danger", f"Error creating job advertisement: {str(e)}"
        )


@router.get("/edit_job_ad_form/{job_ad_id}", response_class=HTMLResponse)
async def get_job_ad_edit_form(
    request: Request,
    job_ad_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the edit form for a job advertisement"""
    auth_response = auth_required_html(
        request, current_user, "You must be logged in to edit job advertisements."
    )
    if auth_response:
        return auth_response

    # Get job ad from database
    job_ad = get_job_ad_service(db=db, job_ad_id=job_ad_id)
    if not job_ad:
        return create_alert_response(
            request,
            "danger",
            f"Job advertisement with ID {job_ad_id} not found.",
            status_code=404,
        )

    # Return the form with job ad data
    return templates.TemplateResponse(
        "partials/edit_job_modal.html",
        {
            "request": request,
            "job": job_ad,
            "form_action": f"/api/v1/job_ads/update_job_ad_form/{job_ad_id}",
        },
    )


@router.post("/update_job_ad_form/{job_ad_id}", response_class=HTMLResponse)
async def update_job_ad_form(
    request: Request,
    job_ad_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Handle job advertisement update form submission with HTMX"""
    auth_response = auth_required_html(
        request, current_user, "You must be logged in to update job advertisements."
    )
    if auth_response:
        return auth_response

    # Process form data
    try:
        form_data = await request.form()
        job_ad_data = process_job_form_data(form_data)
        job_ad = JobAdUpdate(**job_ad_data)

        # Update job ad in database
        updated_job_ad = update_job_ad_service(
            db=db, job_ad_id=job_ad_id, job_ad_update=job_ad
        )

        if not updated_job_ad:
            return create_alert_response(
                request,
                "danger",
                f"Job advertisement with ID {job_ad_id} not found.",
                status_code=404,
            )

        # Return success message with HTMX triggers to close modal and refresh job listings
        return templates.TemplateResponse(
            "partials/alerts.html",
            {
                "request": request,
                "alert_type": "success",
                "message": "Job advertisement updated successfully!",
                "include_refresh_script": True,
                "target_element": "job-listings",
                "refresh_url": "/api/v1/job_ads/get_job_listings_html",
            },
        )
    except Exception as e:
        # Return error message
        return create_alert_response(
            request, "danger", f"Error updating job advertisement: {str(e)}"
        )
