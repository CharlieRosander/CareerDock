from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.job_ad import JobAdBase, JobAdCreate, JobAdUpdate

router = APIRouter()


@router.post("/create_job_ad", response_model=JobAdCreate)
async def create_job_ad(job_ad: JobAdCreate, db: Session = Depends(get_db)):
    pass


@router.put("/update_job_ad/{job_ad_id}", response_model=JobAdUpdate)
async def update_job_ad(
    job_ad_id: int, job_ad: JobAdUpdate, db: Session = Depends(get_db)
):
    pass


@router.delete("/delete_job_ad/{job_ad_id}")
async def delete_job_ad(job_ad_id: int, db: Session = Depends(get_db)):
    pass


@router.get("/get_job_ad/{job_ad_id}", response_model=JobAdBase)
async def get_job_ad(job_ad_id: int, db: Session = Depends(get_db)):
    pass


@router.get("/get_all_job_ads", response_model=List[JobAdBase])
async def get_all_job_ads(db: Session = Depends(get_db)):
    pass
