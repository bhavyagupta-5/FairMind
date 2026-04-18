## FairLens — Backend

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, SQLite, Pandas, Fairlearn, AIF360, SHAP, ReportLab

---

### Local Setup

**Requirements:** Python 3.11+

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Start the server:**
```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

### Run Tests

```bash
pytest tests/ -v
```

---

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/datasets` | List demo datasets |
| GET | `/datasets/{id}/load` | Load a demo dataset |
| POST | `/upload` | Upload a CSV file |
| POST | `/audit` | Start a bias audit |
| GET | `/status/{job_id}` | Poll audit status |
| GET | `/results/{job_id}` | Get audit results |
| GET | `/explain/{job_id}` | Get SHAP explanations |
| POST | `/remediate` | Apply debiasing technique |
| GET | `/report/{job_id}` | Download PDF report |

---

### Demo Datasets

Three datasets are bundled in `backend/datasets/`:

| Dataset | Domain | Protected Attribute | Target |
|---------|--------|-------------------|--------|
| COMPAS Recidivism | Criminal Justice | race, sex | two_year_recid |
| UCI Adult Income | Employment | sex, race | income |
| German Credit | Finance | age, sex | credit_risk |

---

### Docker

```bash
docker build -t fairlens-backend .
docker run -p 8000:8000 fairlens-backend
```

---

### Folder Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app entry point
│   ├── database.py      # SQLAlchemy models
│   └── routers/         # All API endpoints
├── ml/
│   ├── audit.py         # Bias metrics engine (Fairlearn)
│   ├── explain.py       # SHAP explainability engine
│   ├── remediate.py     # Debiasing techniques
│   └── preprocessing.py # Data cleaning utilities
├── reporting/
│   └── pdf_builder.py   # ReportLab PDF generator
├── datasets/            # Bundled demo datasets
├── uploads/             # Runtime CSV storage
├── tests/               # Full pytest test suite
├── requirements.txt
└── Dockerfile
```