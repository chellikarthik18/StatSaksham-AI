from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401 - ensures models are registered on Base.metadata

from app.routers import (
    auth, dashboard, departments, employees, competencies, framework,
    skill_gaps, emerging_skills, courses, programs, learning_paths,
    materials, quiz, analytics, notifications, settings as settings_router,
    ai, employee_portal,
)

app = FastAPI(
    title="StatSaksham AI API",
    description="AI-enabled Skill Intelligence and Learning Platform for official statistics workforce learning.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": True, "detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": True, "detail": exc.errors()})


@app.on_event("startup")
def on_startup():
    # Tables are also created explicitly by seed.py; this is a safety net
    # for first-run convenience (MySQL database itself must already exist).
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(departments.router)
app.include_router(employees.router)
app.include_router(competencies.router)
app.include_router(framework.router)
app.include_router(skill_gaps.router)
app.include_router(emerging_skills.router)
app.include_router(courses.router)
app.include_router(programs.router)
app.include_router(learning_paths.router)
app.include_router(materials.router)
app.include_router(quiz.router)
app.include_router(analytics.router)
app.include_router(notifications.router)
app.include_router(settings_router.router)
app.include_router(ai.router)
app.include_router(employee_portal.router)
