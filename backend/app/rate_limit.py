"""Rate limiting configuration — shared across routers."""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


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
