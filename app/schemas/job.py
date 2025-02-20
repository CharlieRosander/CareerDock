from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional
from decimal import Decimal

class JobBase(BaseModel):
    # Basic info
    title: str
    company: str
    description: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None  # Full-time, Part-time, Contract, etc.
    industry: Optional[str] = None  # Tech, Finance, Healthcare, etc.
    
    # Application details
    status: str
    application_date: datetime
    application_method: Optional[str] = None  # Email, Website, LinkedIn, etc.
    application_url: Optional[HttpUrl] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: Optional[str] = "SEK"  # ISO 4217 currency code
    
    # Contact info
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # Follow-up
    next_follow_up: Optional[datetime] = None
    last_response_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    notes: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    # Basic info
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    industry: Optional[str] = None
    
    # Application details
    status: Optional[str] = None
    application_date: Optional[datetime] = None
    application_method: Optional[str] = None
    application_url: Optional[HttpUrl] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: Optional[str] = None
    
    # Contact info
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # Follow-up
    next_follow_up: Optional[datetime] = None
    last_response_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    notes: Optional[str] = None

class Job(JobBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    ai_parsed: bool
    ai_confidence: Optional[Decimal] = None

    class Config:
        from_attributes = True
