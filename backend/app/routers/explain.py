import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db, Job

router = APIRouter()

@router.get("/explain/{job_id}")
def get_explanation(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    if job.status != "complete":
        raise HTTPException(409, f"Audit not complete. Status: {job.status}")
    if not job.explanation:
        raise HTTPException(404, "Explanation not yet generated")
    result = json.loads(job.explanation)
    result["job_id"] = job_id
    return result