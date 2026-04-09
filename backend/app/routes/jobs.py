from app.config import get_db

# from app.models import Job, User
from app.middleware import verify_token
from app.models import Job
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/")
async def get_jobs(
    current_user_id: int = Depends(verify_token), db: Session = Depends(get_db)
):
    """Get all jobs for current user"""
    jobs = db.query(Job).filter(Job.user_id == current_user_id).all()
    return jobs


@router.post("/")
async def create_job(
    name: str,
    script_path: str,
    cron_schedule: str,
    description: str = None,
    timeout_seconds: int = 300,
    current_user_id: int = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Create a new job"""
    job = Job(
        user_id=current_user_id,
        name=name,
        script_path=script_path,
        cron_schedule=cron_schedule,
        description=description,
        timeout_seconds=timeout_seconds,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    current_user_id: int = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Get specific job"""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    current_user_id: int = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Delete a job"""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"message": "Job deleted"}
