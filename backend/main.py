"""
StatSaksham AI - main FastAPI application entry point.

Run with:
    uvicorn main:app --reload --port 8000
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
import models  # noqa: F401  (ensures models are registered with Base metadata)

from routers import auth, employees, assessments, courses, quizzes, uploads, trainer, admin

load_dotenv()

app = FastAPI(
    title="StatSaksham AI",
    description="Skill Intelligence and Learning Platform for Official Statistics",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS - allow the static HTML/JS frontend to call the API
# ---------------------------------------------------------------------------
origins_env = os.getenv("FRONTEND_ORIGINS", "*")
origins = [o.strip() for o in origins_env.split(",")] if origins_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Create tables if they do not already exist (idempotent).
# For a fresh setup, prefer running `python seed.py` which also creates
# tables and inserts demo data.
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(assessments.router)
app.include_router(courses.router)
app.include_router(quizzes.router)
app.include_router(uploads.router)
app.include_router(trainer.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {
        "app": "StatSaksham AI",
        "title": "StatSaksham AI — Skill Intelligence and Learning Platform for Official Statistics",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
