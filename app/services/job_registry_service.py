from app.schemas.job_ad import JobAdBase, JobAdCreate, JobAdUpdate
from app.core.config import settings
from app.models.jobs import JobAd

from sqlalchemy.orm import Session
from sqlalchemy import update

def create_job_ad(db: Session, job_ad: JobAdCreate) -> JobAd:
    job_ad = JobAd(**job_ad.model_dump())
    db.add(job_ad)
    db.commit()
    return job_ad
