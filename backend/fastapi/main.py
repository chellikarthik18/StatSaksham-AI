# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth
from routers import employees
from routers import skills
from routers import courses
from routers import progress


app = FastAPI(
    title="AI Enabled Learning Platform",
    description=(
        "AI-powered competency assessment and "
        "personalized learning platform"
    ),
    version="1.0.0"
)


# -------------------------
# CORS
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Routers
# -------------------------

app.include_router(
    auth.router,
    prefix="/api"
)

app.include_router(
    employees.router,
    prefix="/api"
)

app.include_router(
    skills.router,
    prefix="/api"
)

app.include_router(
    courses.router,
    prefix="/api"
)

app.include_router(
    progress.router,
    prefix="/api"
)


# -------------------------
# Health check
# -------------------------

@app.get("/")
def root():
    return {
        "message": "AI Learning Platform API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }