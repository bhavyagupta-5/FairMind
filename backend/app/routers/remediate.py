import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db, Job
from ml.remediate import RemediationEngine

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_TECHNIQUES = ["reweighing", "threshold", "adversarial"]


class RemediateRequest(BaseModel):
    job_id: str
    technique: str


@router.post("/remediate")
def remediate(req: RemediateRequest, db: Session = Depends(get_db)):
    # Validate technique
    if req.technique not in VALID_TECHNIQUES:
        raise HTTPException(422, f"Unknown technique '{req.technique}'. Valid: {', '.join(VALID_TECHNIQUES)}")

    # Validate job exists and is complete
    job = db.query(Job).filter(Job.id == req.job_id).first()
    if not job:
        raise HTTPException(404, f"Job {req.job_id} not found")
    if job.status != "complete":
        raise HTTPException(409, f"Audit not complete. Current status: {job.status}")

    results = json.loads(job.results)
    config = json.loads(job.config)
    protected_attr = config["protected_attr"]
    target_col = config["target_col"]
    positive_label = config["positive_label"]
    file_path = job.file_path

    # Run selected technique
    engine = RemediationEngine()
    logger.info("Applying %s for job %s", req.technique, req.job_id)

    if req.technique == "reweighing":
        after = engine.apply_reweighing(file_path, protected_attr, target_col, positive_label)
    elif req.technique == "threshold":
        after = engine.apply_threshold_calibration(file_path, protected_attr, target_col, positive_label)
    else:
        after = engine.apply_adversarial_debiasing(file_path, protected_attr, target_col, positive_label)

    before = results["overall_metrics"]
    before_ratio = round(before["demographic_parity_ratio"], 2)
    after_ratio = round(after["demographic_parity_ratio"], 2)
    improvement = round(after_ratio - before_ratio, 2)
    all_pass = all(v >= 0.8 for v in after["disparate_impact"].values())

    technique_name = req.technique.replace("_", " ").title()
    summary = (
        f"{technique_name} {'improved' if improvement > 0 else 'changed'} the demographic parity "
        f"ratio from {before_ratio} to {after_ratio} "
        f"(a {round(abs(improvement) * 100)}-point {'improvement' if improvement > 0 else 'change'}). "
        f"{'All groups now exceed the EEOC 80% threshold.' if all_pass else 'Some groups still fall below the EEOC threshold.'}"
    )

    response = {
        "job_id": req.job_id,
        "technique": req.technique,
        "before": before,
        "after": after,
        "improvement_summary": summary,
    }

    # Store remediation result in DB
    job.remediation = json.dumps(response)
    db.commit()

    return response