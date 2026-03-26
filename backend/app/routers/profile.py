import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from supabase import Client, create_client

from app.auth import get_current_user_id, get_rls_supabase
from app.config import get_settings
from app.models.profile import ProfileRead, ProfileUpdate
from app.rate_limit import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/", response_model=ProfileRead)
async def get_profile(
    user_id: Annotated[str, Depends(get_current_user_id)],
    sb: Annotated[Client, Depends(get_rls_supabase)],
):
    """Get the current user's profile."""
    result = sb.table("profiles").select("*").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Profil non trouvé")
    return ProfileRead(**result.data[0])


@router.patch("/", response_model=ProfileRead)
async def update_profile(
    updates: ProfileUpdate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    sb: Annotated[Client, Depends(get_rls_supabase)],
):
    """Update the current user's profile."""
    data = updates.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    result = (
        sb.table("profiles")
        .update(data)
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Profil non trouvé")
    return ProfileRead(**result.data[0])


@router.delete("/")
@limiter.limit("3/minute")
async def delete_account(
    request: Request,
    user_id: Annotated[str, Depends(get_current_user_id)],
):
    """Delete the current user's account and all associated data (RGPD)."""
    settings = get_settings()
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

    # Cascade delete user data (order matters for FK constraints)
    sb.table("applications").delete().eq("user_id", user_id).execute()
    sb.table("user_jobs").delete().eq("user_id", user_id).execute()
    sb.table("profiles").delete().eq("id", user_id).execute()

    # Delete auth user via Supabase Admin API
    try:
        sb.auth.admin.delete_user(user_id)
    except Exception as e:
        logger.error(f"Failed to delete auth user {user_id}: {e}")

    return JSONResponse({"status": "deleted"})
