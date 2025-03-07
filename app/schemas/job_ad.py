from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class JobAdBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    job_url: Optional[str] = None
    category: Optional[str] = None
    date_posted: Optional[datetime] = None
    keywords: Optional[List[str]] = None


class JobAdCreate(JobAdBase):
    pass


class JobAdUpdate(JobAdBase):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    job_url: Optional[str] = None
    category: Optional[str] = None
    date_posted: Optional[datetime] = None
    keywords: Optional[List[str]] = None
