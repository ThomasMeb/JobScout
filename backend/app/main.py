import json
import logging

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
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

# Init Sentry (no-op if DSN is empty)
if _settings.sentry_dsn and isinstance(_settings.sentry_dsn, str) and _settings.sentry_dsn.startswith("http"):
    sentry_sdk.init(
        dsn=_settings.sentry_dsn,
        traces_sample_rate=0.2,
        environment=_settings.environment,
    )


def _get_rate_limit_key(request: Request) -> str:
    """Rate limit by user ID (from JWT) when available, fallback to IP.

    NOTE: verify_signature=False is intentional here — this is NOT authentication.
    We only extract the 'sub' claim for rate-limit bucketing. Actual auth happens
    in get_current_user_id() which verifies the signature via Supabase.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        import jwt as pyjwt
        try:
            payload = pyjwt.decode(auth[7:], options={"verify_signature": False})
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_get_rate_limit_key, default_limits=["60/minute"])

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
app.include_router(admin.router)
