import logging

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.routers import billing, health, jobs, profile, scrape_runs, stats

logging.basicConfig(level=logging.INFO)

# Init Sentry before FastAPI (no-op if DSN is empty)
_settings = get_settings()
if _settings.sentry_dsn and isinstance(_settings.sentry_dsn, str) and _settings.sentry_dsn.startswith("http"):
    sentry_sdk.init(
        dsn=_settings.sentry_dsn,
        traces_sample_rate=0.2,
        environment=_settings.environment,
    )

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="JobScout SaaS API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


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
app.include_router(billing.router)
