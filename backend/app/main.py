import json
import logging

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.rate_limit import limiter
from app.routers import admin, billing, health, jobs, profile, scrape_runs, stats


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log)


_settings = get_settings()
handler = logging.StreamHandler()
if _settings.environment != "development":
    handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Init Sentry
if _settings.sentry_dsn and isinstance(_settings.sentry_dsn, str) and _settings.sentry_dsn.startswith("http"):
    sentry_sdk.init(
        dsn=_settings.sentry_dsn,
        traces_sample_rate=0.2,
        environment=_settings.environment,
    )
elif _settings.environment != "development":
    logging.getLogger(__name__).warning("SENTRY_DSN not configured — errors will NOT be tracked in production")


app = FastAPI(
    title="JobScout SaaS API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

logger = logging.getLogger(__name__)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": "Données invalides", "errors": str(exc.errors())})


@app.exception_handler(Exception)
async def generic_error_handler(_request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    sentry_sdk.capture_exception(exc)
    return JSONResponse(status_code=500, content={"detail": "Erreur interne du serveur"})


import time as _time

from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = _time.monotonic()
        response = await call_next(request)
        duration = (_time.monotonic() - start) * 1000
        if not request.url.path.startswith("/api/health"):
            logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.0f}ms)")
        return response


settings = get_settings()

app.add_middleware(RequestLoggingMiddleware)
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
app.include_router(admin.router)
