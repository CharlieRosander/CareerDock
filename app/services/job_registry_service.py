from app.schemas.job_ad import JobAdBase, JobAdCreate, JobAdUpdate
from app.core.config import settings
from app.models.jobs import JobAd

from sqlalchemy.orm import Session
from sqlalchemy import update
from typing import List, Optional
from uuid import UUID

def create_job_ad(db: Session, job_ad: JobAdCreate) -> JobAd:
    """
    Create a new job advertisement in the database.
    
    Args:
        db: Database session
        job_ad: Job advertisement data
        
    Returns:
        The created job advertisement
    """
    job_ad_dict = job_ad.model_dump()
    
    # Convert keywords list to comma-separated string if provided
    if job_ad.keywords:
        job_ad_dict["keywords"] = ",".join(job_ad.keywords)
    
    job_ad_model = JobAd(**job_ad_dict)
    db.add(job_ad_model)
    db.commit()
    db.refresh(job_ad_model)
    return job_ad_model

def get_job_ad(db: Session, job_ad_id: UUID) -> Optional[JobAd]:
    """
    Get a specific job advertisement by ID.
    
    Args:
        db: Database session
        job_ad_id: ID of the job advertisement to retrieve
        
    Returns:
        The job advertisement if found, None otherwise
    """
    return db.query(JobAd).filter(JobAd.id == job_ad_id).first()

def get_all_job_ads(db: Session, skip: int = 0, limit: int = 100) -> List[JobAd]:
    """
    Get all job advertisements with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of job advertisements
    """
    return db.query(JobAd).order_by(JobAd.date_posted.desc()).offset(skip).limit(limit).all()

def update_job_ad(db: Session, job_ad_id: UUID, job_ad_update: JobAdUpdate) -> Optional[JobAd]:
    """
    Update an existing job advertisement.
    
    Args:
        db: Database session
        job_ad_id: ID of the job advertisement to update
        job_ad_update: Updated job advertisement data
        
    Returns:
        The updated job advertisement if found, None otherwise
    """
    job_ad = get_job_ad(db, job_ad_id)
    if not job_ad:
        return None
    
    update_data = job_ad_update.model_dump(exclude_unset=True)
    
    # Convert keywords list to comma-separated string if provided
    if "keywords" in update_data and update_data["keywords"]:
        update_data["keywords"] = ",".join(update_data["keywords"])
    
    # Update the job ad with the new data
    for key, value in update_data.items():
        if value is not None:
            setattr(job_ad, key, value)
    
    db.commit()
    db.refresh(job_ad)
    return job_ad

def delete_job_ad(db: Session, job_ad_id: UUID) -> bool:
    """
    Delete a job advertisement.
    
    Args:
        db: Database session
        job_ad_id: ID of the job advertisement to delete
        
    Returns:
        True if the job advertisement was deleted, False otherwise
    """
    job_ad = get_job_ad(db, job_ad_id)
    if not job_ad:
        return False
    
    db.delete(job_ad)
    db.commit()
    return True

def search_job_ads(db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[JobAd]:
    """
    Search for job advertisements by title, company, or keywords.
    
    Args:
        db: Database session
        search_term: Term to search for
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of matching job advertisements
    """
    search_pattern = f"%{search_term}%"
    return db.query(JobAd).filter(
        (JobAd.title.ilike(search_pattern)) |
        (JobAd.company.ilike(search_pattern)) |
        (JobAd.keywords.ilike(search_pattern)) |
        (JobAd.description.ilike(search_pattern))
    ).order_by(JobAd.date_posted.desc()).offset(skip).limit(limit).all()


def process_job_form_data(form_data: dict) -> dict:
    """
    Process form data for job ad creation/update.
    
    Args:
        form_data: Form data from request
        
    Returns:
        Processed job ad data ready for schema creation
    """
    job_ad_data = {
        "title": form_data.get("title"),
        "company": form_data.get("company"),
        "location": form_data.get("location"),
        "description": form_data.get("description"),
        "job_url": form_data.get("job_url"),
        "category": form_data.get("category"),
    }
    
    # Handle keywords (convert from comma-separated string to list)
    keywords = form_data.get("keywords")
    if keywords:
        job_ad_data["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]
    
    return job_ad_data


def get_job_listings(db: Session, search_term: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[JobAd]:
    """
    Get job listings, optionally filtered by search term.
    
    Args:
        db: Database session
        search_term: Optional search term to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of job advertisements
    """
    if search_term:
        return search_job_ads(db=db, search_term=search_term, skip=skip, limit=limit)
    else:
        return get_all_job_ads(db=db, skip=skip, limit=limit)
