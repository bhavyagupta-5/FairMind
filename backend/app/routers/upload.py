import os
import uuid
import logging
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db, Job

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 50
MIN_ROWS = 50


def get_base_dir():
    # Go up 3 levels: routers → app → backend
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(422, f"File must be a CSV. Received: {file.content_type}")

    contents = await file.read()

    # Validate file size
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(422, f"File too large ({size_mb:.1f}MB). Maximum allowed: {MAX_FILE_SIZE_MB}MB")

    # Save file
    base_dir = get_base_dir()
    upload_dir = os.path.join(base_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    job_id = str(uuid.uuid4())[:8]
    file_path = os.path.join(upload_dir, f"{job_id}.csv")

    with open(file_path, "wb") as f:
        f.write(contents)

    # Validate CSV content
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(422, f"Could not parse CSV file: {str(e)}")

    if len(df) < MIN_ROWS:
        os.remove(file_path)
        raise HTTPException(422, f"Dataset too small ({len(df)} rows). Minimum required: {MIN_ROWS} rows")

    if len(df.columns) < 2:
        os.remove(file_path)
        raise HTTPException(422, "CSV must have at least 2 columns")

    # Create job record
    job = Job(id=job_id, status="uploaded", file_path=file_path)
    db.add(job)
    db.commit()

    logger.info("File uploaded: %s (%d rows, %d cols)", file.filename, len(df), len(df.columns))

    return {
        "job_id": job_id,
        "columns": list(df.columns),
        "preview": df.head(10).values.tolist(),
        "row_count": len(df),
    }


@router.get("/datasets")
def list_datasets():
    return [
        {"id": "compas", "name": "COMPAS Recidivism", "domain": "Criminal Justice",
         "rows": 7214, "protected_attrs": ["race", "sex"], "target": "two_year_recid",
         "description": "Predicts likelihood of reoffending. Known for racial bias."},
        {"id": "adult", "name": "UCI Adult Income", "domain": "Employment",
         "rows": 48842, "protected_attrs": ["sex", "race"], "target": "income",
         "description": "Predicts income >50K. Known for gender and racial bias."},
        {"id": "german", "name": "German Credit", "domain": "Finance",
         "rows": 1000, "protected_attrs": ["age", "sex"], "target": "credit_risk",
         "description": "Predicts credit risk. Known for age and gender bias."},
    ]


@router.get("/datasets/{dataset_id}/load")
def load_demo_dataset(dataset_id: str, db: Session = Depends(get_db)):
    valid_ids = ["compas", "adult", "german"]
    if dataset_id not in valid_ids:
        raise HTTPException(404, f"Dataset '{dataset_id}' not found. Valid ids: {', '.join(valid_ids)}")

    base_dir = get_base_dir()
    file_path = os.path.join(base_dir, "datasets", f"{dataset_id}.csv")

    if not os.path.exists(file_path):
        raise HTTPException(404, f"Dataset file not found on server: {file_path}")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(500, f"Failed to load dataset: {str(e)}")

    job_id = f"demo_{dataset_id}_{str(uuid.uuid4())[:6]}"
    job = Job(id=job_id, status="uploaded", file_path=file_path, dataset_id=dataset_id)
    db.add(job)
    db.commit()

    logger.info("Demo dataset loaded: %s → job %s", dataset_id, job_id)

    return {
        "job_id": job_id,
        "columns": list(df.columns),
        "preview": df.head(10).values.tolist(),
        "row_count": len(df),
    }