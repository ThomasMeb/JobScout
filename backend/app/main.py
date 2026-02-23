import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, jobs, profile, scrape_runs, stats

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="JobScout SaaS API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
app.include_router(profile.router)
app.include_router(jobs.router)
app.include_router(stats.router)
app.include_router(scrape_runs.router)
