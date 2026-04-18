import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BACKEND_DIR, "datasets")
COMPAS_PATH = os.path.join(DATASETS_DIR, "compas.csv")


# ── Health ─────────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ── Datasets ───────────────────────────────────────────────────────────────────

def test_datasets_returns_three():
    r = client.get("/datasets")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    ids = [d["id"] for d in data]
    assert "compas" in ids
    assert "adult" in ids
    assert "german" in ids


def test_datasets_have_required_fields():
    r = client.get("/datasets")
    for dataset in r.json():
        assert "id" in dataset
        assert "name" in dataset
        assert "domain" in dataset
        assert "rows" in dataset
        assert "protected_attrs" in dataset
        assert "target" in dataset


def test_load_compas_demo_dataset():
    r = client.get("/datasets/compas/load")
    assert r.status_code == 200
    data = r.json()
    assert "job_id" in data
    assert "columns" in data
    assert "row_count" in data
    assert data["row_count"] > 0
    assert "race" in data["columns"]
    assert "two_year_recid" in data["columns"]


def test_load_invalid_dataset_returns_404():
    r = client.get("/datasets/nonexistent/load")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


# ── Upload ─────────────────────────────────────────────────────────────────────

def test_upload_valid_csv():
    with open(COMPAS_PATH, "rb") as f:
        r = client.post("/upload", files={"file": ("compas.csv", f, "text/csv")})
    assert r.status_code == 200
    data = r.json()
    assert "job_id" in data
    assert "columns" in data
    assert "row_count" in data
    assert len(data["columns"]) > 0


def test_upload_invalid_file_type():
    r = client.post(
        "/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")}
    )
    assert r.status_code == 422
    assert "csv" in r.json()["detail"].lower()


def test_upload_too_small_csv():
    # Create a tiny CSV with fewer than 50 rows
    tiny_csv = "col1,col2\n" + "\n".join([f"{i},{i}" for i in range(10)])
    r = client.post(
        "/upload",
        files={"file": ("tiny.csv", tiny_csv.encode(), "text/csv")}
    )
    assert r.status_code == 422
    assert "small" in r.json()["detail"].lower()


# ── Audit ──────────────────────────────────────────────────────────────────────

def test_audit_invalid_job_id():
    r = client.post("/audit", json={
        "job_id": "nonexistent_job",
        "protected_attr": "race",
        "target_col": "two_year_recid",
        "positive_label": "1"
    })
    assert r.status_code == 404


def test_audit_invalid_protected_attr():
    # First create a valid job
    load_r = client.get("/datasets/compas/load")
    job_id = load_r.json()["job_id"]

    r = client.post("/audit", json={
        "job_id": job_id,
        "protected_attr": "nonexistent_column",
        "target_col": "two_year_recid",
        "positive_label": "1"
    })
    assert r.status_code == 422
    assert "nonexistent_column" in r.json()["detail"]


def test_audit_invalid_positive_label():
    load_r = client.get("/datasets/compas/load")
    job_id = load_r.json()["job_id"]

    r = client.post("/audit", json={
        "job_id": job_id,
        "protected_attr": "race",
        "target_col": "two_year_recid",
        "positive_label": "99"
    })
    assert r.status_code == 422
    assert "99" in r.json()["detail"]


def test_audit_starts_successfully():
    load_r = client.get("/datasets/compas/load")
    job_id = load_r.json()["job_id"]

    r = client.post("/audit", json={
        "job_id": job_id,
        "protected_attr": "race",
        "target_col": "two_year_recid",
        "positive_label": "1"
    })
    assert r.status_code == 200
    assert r.json()["status"] == "processing"


# ── Status ─────────────────────────────────────────────────────────────────────

def test_status_invalid_job_returns_404():
    r = client.get("/status/nonexistent_job")
    assert r.status_code == 404


def test_status_has_required_fields():
    load_r = client.get("/datasets/compas/load")
    job_id = load_r.json()["job_id"]

    r = client.get(f"/status/{job_id}")
    assert r.status_code == 200
    data = r.json()
    assert "job_id" in data
    assert "status" in data
    assert "progress" in data
    assert "progress_message" in data


# ── Results ────────────────────────────────────────────────────────────────────

def test_results_returns_409_if_not_complete():
    load_r = client.get("/datasets/compas/load")
    job_id = load_r.json()["job_id"]
    # Don't run audit — status is still "uploaded"
    r = client.get(f"/results/{job_id}")
    assert r.status_code == 409


def test_results_invalid_job_returns_404():
    r = client.get("/results/nonexistent_job")
    assert r.status_code == 404


# ── Remediate ──────────────────────────────────────────────────────────────────

def test_remediate_invalid_technique():
    load_r = client.get("/datasets/compas/load")
    job_id = load_r.json()["job_id"]

    r = client.post("/remediate", json={
        "job_id": job_id,
        "technique": "invalid_technique"
    })
    assert r.status_code == 422
    assert "invalid_technique" in r.json()["detail"]


def test_remediate_on_incomplete_job_returns_409():
    load_r = client.get("/datasets/compas/load")
    job_id = load_r.json()["job_id"]
    # Don't run audit first
    r = client.post("/remediate", json={
        "job_id": job_id,
        "technique": "reweighing"
    })
    assert r.status_code == 409


# ── Report ─────────────────────────────────────────────────────────────────────

def test_report_on_incomplete_job_returns_404():
    load_r = client.get("/datasets/compas/load")
    job_id = load_r.json()["job_id"]
    r = client.get(f"/report/{job_id}")
    assert r.status_code == 404


def test_report_invalid_job_returns_404():
    r = client.get("/report/nonexistent_job")
    assert r.status_code == 404