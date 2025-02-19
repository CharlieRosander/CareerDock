from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime

from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate


class JobService:
    def __init__(self, db: Session):
        self.db = db

    def get_job(self, job_id: int, user_id: int) -> Optional[Job]:
        """Get a specific job"""
        return (
            self.db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        )

    def get_user_jobs(self, user_id: int) -> List[Job]:
        """Get all jobs for a user"""
        return (
            self.db.query(Job)
            .filter(Job.user_id == user_id)
            .order_by(Job.updated_at.desc())
            .all()
        )

    def create_job(self, user_id: int, job_data: JobCreate) -> Job:
        """Create a new job"""
        db_job = Job(
            user_id=user_id,
            title=job_data.title,
            company=job_data.company,
            description=job_data.description,
            status=job_data.status,
            application_date=job_data.application_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)
        return db_job

    def update_job(
        self, job_id: int, user_id: int, job_data: JobUpdate
    ) -> Optional[Job]:
        """Update a job"""
        db_job = self.get_job(job_id, user_id)
        if not db_job:
            return None

        # Update fields
        for field, value in job_data.dict(exclude_unset=True).items():
            setattr(db_job, field, value)

        db_job.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_job)
        return db_job

    def delete_job(self, job_id: int, user_id: int) -> bool:
        """Delete a job"""
        db_job = self.get_job(job_id, user_id)
        if not db_job:
            return False

        self.db.delete(db_job)
        self.db.commit()
        return True

    def search_jobs(self, user_id: int, query: str) -> List[Job]:
        """Search for jobs based on title, company or description"""
        return (
            self.db.query(Job)
            .filter(
                Job.user_id == user_id,
                or_(
                    Job.title.ilike(f"%{query}%"),
                    Job.company.ilike(f"%{query}%"),
                    Job.description.ilike(f"%{query}%"),
                ),
            )
            .order_by(Job.updated_at.desc())
            .all()
        )

    def filter_jobs(self, user_id: int, status: str) -> List[Job]:
        """Filter jobs by status"""
        query = self.db.query(Job).filter(Job.user_id == user_id)

        if status != "all":
            query = query.filter(Job.status == status)

        return query.order_by(Job.updated_at.desc()).all()
