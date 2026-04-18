import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload, audit, explain, remediate, report
from app.database import create_tables

# Configure logging for the whole app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(title="FairLens API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://fairlens.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

app.include_router(upload.router)
app.include_router(audit.router)
app.include_router(explain.router)
app.include_router(remediate.router)
app.include_router(report.router)

@app.get("/health")
def health():
    return {"status": "ok"}