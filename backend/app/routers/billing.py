"""Stripe billing endpoints for subscription management."""
import logging
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from supabase import create_client

from app.auth import get_current_user_id
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])


def _get_stripe():
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Facturation non configurée")
    stripe.api_key = settings.stripe_secret_key
    return stripe


def _get_admin_sb():
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@router.get("/status")
async def billing_status(
    user_id: Annotated[str, Depends(get_current_user_id)],
):
    """Get current user's billing status."""
    sb = _get_admin_sb()
    profile = (
        sb.table("profiles")
        .select("plan, stripe_customer_id, stripe_subscription_id, plan_expires_at, trial_started_at")
        .eq("id", user_id)
        .single()
        .execute()
    )
    data = profile.data or {}
    return {
        "plan": data.get("plan", "free"),
        "has_subscription": bool(data.get("stripe_subscription_id")),
        "plan_expires_at": data.get("plan_expires_at"),
        "trial_started_at": data.get("trial_started_at"),
    }


@router.post("/checkout")
async def create_checkout(
    user_id: Annotated[str, Depends(get_current_user_id)],
):
    """Create a Stripe Checkout session for Pro subscription."""
    settings = get_settings()
    s = _get_stripe()
    sb = _get_admin_sb()

    # Get or create Stripe customer
    profile = (
        sb.table("profiles")
        .select("stripe_customer_id, notification_email, name")
        .eq("id", user_id)
        .single()
        .execute()
    )
    data = profile.data or {}
    customer_id = data.get("stripe_customer_id")

    if not customer_id:
        customer = s.Customer.create(
            email=data.get("notification_email"),
            name=data.get("name"),
            metadata={"user_id": user_id},
        )
        customer_id = customer.id
        sb.table("profiles").update({"stripe_customer_id": customer_id}).eq("id", user_id).execute()

    session = s.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": settings.stripe_pro_price_id, "quantity": 1}],
        success_url=f"{settings.frontend_url}/dashboard?billing=success",
        cancel_url=f"{settings.frontend_url}/pricing",
        metadata={"user_id": user_id},
    )

    return {"checkout_url": session.url}


@router.post("/portal")
async def create_portal(
    user_id: Annotated[str, Depends(get_current_user_id)],
):
    """Create a Stripe Customer Portal session for managing subscription."""
    settings = get_settings()
    s = _get_stripe()
    sb = _get_admin_sb()

    profile = (
        sb.table("profiles")
        .select("stripe_customer_id")
        .eq("id", user_id)
        .single()
        .execute()
    )
    customer_id = (profile.data or {}).get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="Aucun compte de facturation trouvé")

    session = s.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.frontend_url}/settings",
    )

    return {"portal_url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook non configuré")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        stripe.api_key = settings.stripe_secret_key
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Signature invalide")

    sb = _get_admin_sb()
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
        if customer_id and subscription_id:
            sb.table("profiles").update({
                "plan": "pro",
                "stripe_subscription_id": subscription_id,
                "plan_expires_at": None,
            }).eq("stripe_customer_id", customer_id).execute()
            logger.info(f"Activated Pro plan for customer {customer_id}")

    elif event_type in ("customer.subscription.updated", "customer.subscription.renewed"):
        customer_id = data.get("customer")
        status = data.get("status")
        if status == "active":
            sb.table("profiles").update({
                "plan": "pro",
                "plan_expires_at": None,
            }).eq("stripe_customer_id", customer_id).execute()

    elif event_type in ("customer.subscription.deleted", "customer.subscription.paused"):
        customer_id = data.get("customer")
        sb.table("profiles").update({
            "plan": "free",
            "stripe_subscription_id": None,
            "plan_expires_at": None,
        }).eq("stripe_customer_id", customer_id).execute()
        logger.info(f"Downgraded to Free for customer {customer_id}")

    elif event_type == "invoice.payment_failed":
        customer_id = data.get("customer")
        logger.warning(f"Payment failed for customer {customer_id}")

    return JSONResponse({"status": "ok"})
