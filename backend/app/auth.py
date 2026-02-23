import logging
from typing import Annotated

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from app.config import Settings, get_settings
from app.db import make_user_client

logger = logging.getLogger(__name__)

security = HTTPBearer()

_jwk_client: PyJWKClient | None = None


def _get_jwk_client(settings: Settings) -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        _jwk_client = PyJWKClient(jwks_url, headers={"apikey": settings.supabase_anon_key})
    return _jwk_client


def verify_supabase_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Verify Supabase JWT and return decoded payload.

    Returns dict with at least 'sub' (user UUID) and 'email'.
    """
    token = credentials.credentials
    try:
        # Get signing key from JWKS endpoint
        jwk_client = _get_jwk_client(settings)
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
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


def get_rls_supabase(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    _user_id: Annotated[str, Depends(get_current_user_id)],
) -> Client:
    """Get Supabase client with user's JWT for RLS enforcement.

    Depends on get_current_user_id to ensure the token is verified
    before creating the client. FastAPI caches the security dependency
    so credentials are only extracted once per request.
    """
    return make_user_client(credentials.credentials)
