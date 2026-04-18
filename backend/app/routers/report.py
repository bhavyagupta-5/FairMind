import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db, Job
from reporting.pdf_builder import PDFBuilder

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/report/{job_id}")
def download_report(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != "complete":
        raise HTTPException(404, "Report not available. Audit must be complete first.")

    results = json.loads(job.results)
    explanation = json.loads(job.explanation) if job.explanation else None
    remediation = json.loads(job.remediation) if job.remediation else None

    logger.info("Generating PDF report for job %s", job_id)
    pdf_bytes = PDFBuilder().build(results, explanation, remediation)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="FairLens_Audit_{job_id}.pdf"'
        }
    )