import logging
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


def verify_supabase_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Verify Supabase JWT and return decoded payload.

    Returns dict with at least 'sub' (user UUID) and 'email'.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_current_user_id(
    payload: Annotated[dict, Depends(verify_supabase_token)],
) -> str:
    """Extract user UUID from verified JWT payload."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: no user ID",
        )
    return user_id
