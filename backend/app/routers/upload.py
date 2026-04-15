import uuid, os, json
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db, Job

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(422, f"File must be a CSV. Received: {file.content_type}")

    job_id = str(uuid.uuid4())[:8]
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}.csv")
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    df = pd.read_csv(file_path)
    columns = list(df.columns)
    preview = df.head(10).values.tolist()
    row_count = len(df)

    job = Job(id=job_id, status="uploaded", file_path=file_path)
    db.add(job)
    db.commit()

    return {"job_id": job_id, "columns": columns, "preview": preview, "row_count": row_count}

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

    file_path = f"datasets/{dataset_id}.csv"
    df = pd.read_csv(file_path)
    job_id = f"demo_{dataset_id}_{str(uuid.uuid4())[:6]}"
    job = Job(id=job_id, status="uploaded", file_path=file_path, dataset_id=dataset_id)
    db.add(job)
    db.commit()

    return {
        "job_id": job_id,
        "columns": list(df.columns),
        "preview": df.head(10).values.tolist(),
        "row_count": len(df),
    }