import json
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db, Job

router = APIRouter()
logger = logging.getLogger(__name__)


class AuditRequest(BaseModel):
    job_id: str
    protected_attr: str
    target_col: str
    positive_label: str


@router.post("/audit")
def start_audit(req: AuditRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check job exists
    job = db.query(Job).filter(Job.id == req.job_id).first()
    if not job:
        raise HTTPException(404, f"Job {req.job_id} not found")

    # Validate columns exist in the CSV
    import pandas as pd
    df = pd.read_csv(job.file_path)

    if req.protected_attr not in df.columns:
        raise HTTPException(422, f"Column '{req.protected_attr}' not found. Available: {list(df.columns)}")
    if req.target_col not in df.columns:
        raise HTTPException(422, f"Column '{req.target_col}' not found. Available: {list(df.columns)}")

    valid_labels = df[req.target_col].astype(str).unique().tolist()
    if req.positive_label not in valid_labels:
        raise HTTPException(422, f"Label '{req.positive_label}' not in target column. Found: {valid_labels}")

    # Save config to DB
    job.config = json.dumps({
        "protected_attr": req.protected_attr,
        "target_col": req.target_col,
        "positive_label": req.positive_label,
    })
    job.status = "processing"
    job.progress = 5
    job.progress_message = "Starting audit..."
    db.commit()

    # Launch background task
    background_tasks.add_task(
        run_audit_task,
        req.job_id,
        job.file_path,
        req.protected_attr,
        req.target_col,
        req.positive_label
    )

    return {"job_id": req.job_id, "status": "processing"}


@router.get("/status/{job_id}")
def get_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    return {
        "job_id": job_id,
        "status": job.status,
        "progress": job.progress,
        "progress_message": job.progress_message,
    }


@router.get("/results/{job_id}")
def get_results(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    if job.status != "complete":
        raise HTTPException(409, f"Audit not yet complete. Current status: {job.status}")
    return json.loads(job.results)


# ── Background task — runs AFTER the endpoint returns ─────────────────────────
def run_audit_task(job_id, file_path, protected_attr, target_col, positive_label):
    from app.database import SessionLocal
    from ml.audit import AuditEngine
    from ml.explain import ExplainEngine

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        def update(progress, message):
            job.progress = progress
            job.progress_message = message
            db.commit()
            logger.info("[%s] %d%% — %s", job_id, progress, message)

        update(10, "Loading and cleaning dataset...")
        engine = AuditEngine()

        update(30, "Training baseline model...")
        results = engine.run(
            file_path, protected_attr, target_col, positive_label,
            update_fn=update
        )
        results["job_id"] = job_id
        job.results = json.dumps(results)

        update(85, "Running explainability analysis...")
        try:
            explain_engine = ExplainEngine()
            explanation = explain_engine.run(
                engine.model, engine.X_test, engine.y_test,
                engine.X_test_raw, protected_attr, engine.groups
            )
            explanation["job_id"] = job_id
            job.explanation = json.dumps(explanation)
        except Exception as e:
            # Explainability failure should not crash the whole audit
            logger.warning("Explainability failed for job %s: %s", job_id, str(e))
            job.explanation = json.dumps({
                "job_id": job_id,
                "features": [],
                "group_shap": {},
                "top_bias_drivers": []
            })

        update(100, "Complete")
        job.status = "complete"
        db.commit()
        logger.info("Audit complete for job %s — verdict: %s", job_id, results.get("verdict"))

    except Exception as e:
        logger.error("Audit failed for job %s: %s", job_id, str(e))
        job.status = "error"
        job.progress_message = f"Error: {str(e)}"
        db.commit()
        raise
    finally:
        db.close()