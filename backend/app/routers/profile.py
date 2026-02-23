import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.auth import get_current_user_id, get_rls_supabase
from app.models.profile import ProfileRead, ProfileUpdate

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
        raise HTTPException(status_code=404, detail="Profile not found")
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
        raise HTTPException(status_code=400, detail="No fields to update")

    result = (
        sb.table("profiles")
        .update(data)
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileRead(**result.data[0])
