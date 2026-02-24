"""Auto-apply — email extraction + automatic application sending via Resend."""
import base64
import logging
import re
from datetime import datetime, timezone

import httpx

from worker.config import get_settings
from worker.db import get_supabase

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"

# Emails to ignore when extracting from job postings
IGNORED_EMAIL_PATTERNS = {
    "noreply", "no-reply", "no_reply",
    "privacy", "abuse", "postmaster",
    "mailer-daemon", "unsubscribe",
    "info@indeed", "info@linkedin",
    "support@indeed", "support@linkedin",
}


def extract_email_from_job(apply_url: str | None, description: str | None) -> str | None:
    """Extract a contact email from job apply_url or description.

    Priority:
    1. mailto: link in apply_url
    2. Email pattern in apply_url
    3. Email pattern in job description
    Filters out noreply/automated addresses.
    """
    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

    # 1. mailto: in apply_url
    if apply_url:
        mailto_match = re.search(r"mailto:([^?&\s]+)", apply_url)
        if mailto_match:
            email = mailto_match.group(1).strip().lower()
            if _is_valid_contact_email(email):
                return email

        # 2. Email in apply_url
        url_match = re.search(email_regex, apply_url)
        if url_match:
            email = url_match.group(0).lower()
            if _is_valid_contact_email(email):
                return email

    # 3. Email in description
    if description:
        for match in re.finditer(email_regex, description):
            email = match.group(0).lower()
            if _is_valid_contact_email(email):
                return email

    return None


def _is_valid_contact_email(email: str) -> bool:
    """Check that the email is a real contact address, not automated."""
    local_part = email.split("@")[0].lower()
    domain = email.split("@")[1].lower() if "@" in email else ""

    for pattern in IGNORED_EMAIL_PATTERNS:
        if pattern in local_part or pattern in domain:
            return False

    return True


async def send_application_email(
    to_email: str,
    user_name: str,
    job_title: str,
    company: str,
    cover_letter: str,
    cv_pdf_bytes: bytes,
    reply_to: str | None = None,
) -> bool:
    """Send application email via Resend API with CV PDF attachment."""
    settings = get_settings()

    if not settings.resend_api_key:
        logger.warning("Resend API key not configured, cannot send application email")
        return False

    cv_b64 = base64.b64encode(cv_pdf_bytes).decode("utf-8")

    payload = {
        "from": f"{user_name} via JobScout <{settings.auto_apply_from_email}>",
        "to": [to_email],
        "subject": f"Candidature - {job_title} - {user_name}",
        "html": cover_letter,
        "attachments": [
            {
                "filename": f"CV_{user_name.replace(' ', '_')}.pdf",
                "content": cv_b64,
            }
        ],
    }

    if reply_to:
        payload["reply_to"] = reply_to

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code in (200, 201):
                logger.info(f"Application email sent to {to_email} for {job_title} @ {company}")
                return True
            logger.error(f"Resend API error {resp.status_code}: {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Failed to send application email to {to_email}: {e}")
            return False


async def try_auto_apply(user_id: str, user_job_id: int, bot, chat_id: int) -> dict:
    """Attempt to auto-send application for a validated job.

    1. Fetch application data (CV PDF + cover letter) from applications table
    2. Fetch job info (apply_url, description)
    3. Extract email from apply_url or description
    4. If email found → send via Resend API
    5. If no email → return apply_url for manual application

    Returns: {"sent": bool, "email": str|None, "apply_url": str|None}
    """
    settings = get_settings()
    if not settings.auto_apply_enabled:
        return {"sent": False, "email": None, "apply_url": None}

    sb = get_supabase()

    # Fetch application
    app_result = (
        sb.table("applications")
        .select("cover_letter_text, cv_pdf_url")
        .eq("user_job_id", user_job_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    application = (app_result.data or [None])[0]
    if not application:
        logger.warning(f"No application found for user_job {user_job_id}")
        return {"sent": False, "email": None, "apply_url": None}

    # Fetch job info
    uj_result = (
        sb.table("user_jobs")
        .select("raw_jobs(title, company, apply_url, source_url, description)")
        .eq("id", user_job_id)
        .single()
        .execute()
    )
    raw = (uj_result.data or {}).get("raw_jobs", {})
    apply_url = raw.get("apply_url") or raw.get("source_url")
    description = raw.get("description")

    # Extract email
    email = extract_email_from_job(apply_url, description)

    if not email:
        return {"sent": False, "email": None, "apply_url": apply_url}

    # Get user profile info
    profile = (
        sb.table("profiles")
        .select("name, notification_email")
        .eq("id", user_id)
        .single()
        .execute()
    )
    user_name = (profile.data or {}).get("name") or "Candidat"
    reply_to = (profile.data or {}).get("notification_email")

    # Get CV PDF bytes
    cv_pdf_bytes = None
    cv_pdf_url = application.get("cv_pdf_url")
    if cv_pdf_url:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(cv_pdf_url)
                if resp.status_code == 200:
                    cv_pdf_bytes = resp.content
        except Exception as e:
            logger.error(f"Failed to download CV PDF: {e}")

    if not cv_pdf_bytes:
        logger.warning(f"No CV PDF available for user_job {user_job_id}, skipping auto-apply")
        return {"sent": False, "email": email, "apply_url": apply_url}

    cover_letter = application.get("cover_letter_text") or ""

    sent = await send_application_email(
        to_email=email,
        user_name=user_name,
        job_title=raw.get("title", ""),
        company=raw.get("company", ""),
        cover_letter=cover_letter,
        cv_pdf_bytes=cv_pdf_bytes,
        reply_to=reply_to,
    )

    if sent:
        # Record the send in the application
        sb.table("applications").update({
            "status": "sent",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "sent_to_email": email,
        }).eq("user_job_id", user_job_id).order("created_at", desc=True).limit(1).execute()

    return {"sent": sent, "email": email, "apply_url": apply_url}
