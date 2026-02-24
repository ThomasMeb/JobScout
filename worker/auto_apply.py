"""Auto-apply — email extraction, mailto link generation, and optional direct sending."""
import base64
import logging
import re
from datetime import datetime, timezone
from urllib.parse import quote

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


def build_mailto_link(to_email: str, subject: str, body: str) -> str:
    """Build a mailto: link with pre-filled subject and body."""
    return f"mailto:{to_email}?subject={quote(subject)}&body={quote(body)}"


async def prepare_apply_info(user_id: str, user_job_id: int) -> dict:
    """Prepare all application info for the validate step.

    Returns: {
        "email": str|None,        - extracted recruiter email
        "mailto_link": str|None,  - pre-filled mailto: link
        "apply_url": str|None,    - original job listing URL
        "subject": str,           - email subject line
        "user_name": str,         - candidate name
    }
    """
    sb = get_supabase()

    # Fetch application (cover letter for mailto body)
    app_result = (
        sb.table("applications")
        .select("cover_letter")
        .eq("user_job_id", user_job_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    application = (app_result.data or [None])[0]

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
    job_title = raw.get("title", "")

    # Get user profile info
    profile = (
        sb.table("profiles")
        .select("name")
        .eq("id", user_id)
        .single()
        .execute()
    )
    user_name = (profile.data or {}).get("name") or "Candidat"

    # Extract email
    email = extract_email_from_job(apply_url, description)

    # Build mailto link if email found
    mailto_link = None
    subject = f"Candidature - {job_title} - {user_name}"
    if email and application:
        # Use plain text version of cover letter for mailto body
        cover_letter = application.get("cover_letter") or ""
        # Strip HTML tags for plain text mailto body
        body_text = re.sub(r"<[^>]+>", "", cover_letter).strip()
        mailto_link = build_mailto_link(email, subject, body_text)

    return {
        "email": email,
        "mailto_link": mailto_link,
        "apply_url": apply_url,
        "subject": subject,
        "user_name": user_name,
    }


# ---------------------------------------------------------------------------
# Direct send (solo mode — requires SMTP/API config)
# ---------------------------------------------------------------------------

async def send_application_email(
    to_email: str,
    user_name: str,
    job_title: str,
    company: str,
    cover_letter: str,
    cv_pdf_bytes: bytes,
    reply_to: str | None = None,
) -> bool:
    """Send application email via Resend API with CV PDF attachment.

    Used only in solo mode when auto_apply_enabled=True and API key is configured.
    """
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


async def try_auto_send(user_id: str, user_job_id: int) -> dict:
    """Solo mode: attempt direct email send.

    Returns: {"sent": bool, "email": str|None, "apply_url": str|None}
    """
    settings = get_settings()
    if not settings.auto_apply_enabled or not settings.resend_api_key:
        return {"sent": False, "email": None, "apply_url": None}

    sb = get_supabase()

    # Fetch application
    app_result = (
        sb.table("applications")
        .select("cover_letter, cv_storage_path")
        .eq("user_job_id", user_job_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    application = (app_result.data or [None])[0]
    if not application:
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
    email = extract_email_from_job(apply_url, raw.get("description"))

    if not email:
        return {"sent": False, "email": None, "apply_url": apply_url}

    # Get user profile
    profile = (
        sb.table("profiles")
        .select("name, notification_email")
        .eq("id", user_id)
        .single()
        .execute()
    )
    user_name = (profile.data or {}).get("name") or "Candidat"
    reply_to = (profile.data or {}).get("notification_email")

    # Download CV PDF
    cv_pdf_bytes = None
    cv_storage_path = application.get("cv_storage_path")
    if cv_storage_path:
        try:
            cv_pdf_bytes = sb.storage.from_("applications").download(cv_storage_path)
        except Exception as e:
            logger.error(f"Failed to download CV PDF from storage: {e}")

    if not cv_pdf_bytes:
        return {"sent": False, "email": email, "apply_url": apply_url}

    sent = await send_application_email(
        to_email=email,
        user_name=user_name,
        job_title=raw.get("title", ""),
        company=raw.get("company", ""),
        cover_letter=application.get("cover_letter") or "",
        cv_pdf_bytes=cv_pdf_bytes,
        reply_to=reply_to,
    )

    if sent:
        sb.table("applications").update({
            "status": "sent",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "sent_to_email": email,
        }).eq("user_job_id", user_job_id).order("created_at", desc=True).limit(1).execute()

    return {"sent": sent, "email": email, "apply_url": apply_url}
