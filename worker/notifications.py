"""Email notifications for scored jobs.

Sends a digest email to users who have new high-scoring jobs
since their last notification. Uses Resend API.
"""
import logging
from datetime import datetime, timezone

import httpx

from worker.config import get_settings
from worker.db import get_supabase

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


async def send_notifications():
    """Send email digests to users with new unnotified high-score jobs."""
    settings = get_settings()
    if not settings.resend_api_key:
        logger.info("No RESEND_API_KEY configured, skipping email notifications")
        return

    sb = get_supabase()

    # Get users with email notifications enabled
    profiles = (
        sb.table("profiles")
        .select("id, name, notification_email, min_score_notify")
        .eq("onboarding_completed", True)
        .not_.is_("notification_email", "null")
        .execute()
    )

    if not profiles.data:
        return

    total_sent = 0

    for user in profiles.data:
        user_id = user["id"]
        email = user.get("notification_email")
        if not email:
            continue

        min_score = user.get("min_score_notify") or 70

        # Get unnotified jobs above threshold
        new_jobs = (
            sb.table("user_jobs")
            .select("id, match_score, match_priority, match_keywords, raw_jobs(title, company, location, source_url)")
            .eq("user_id", user_id)
            .gte("match_score", min_score)
            .is_("notified_at", "null")
            .order("match_score", desc=True)
            .limit(20)
            .execute()
        )

        jobs = new_jobs.data or []
        if not jobs:
            continue

        # Build email
        name = user.get("name") or "there"
        html = _build_digest_html(name, jobs)
        subject = f"JobScout: {len(jobs)} new job{'s' if len(jobs) > 1 else ''} matching your profile"

        # Send via Resend
        sent = await _send_email(
            settings.resend_api_key,
            settings.notification_from_email,
            email,
            subject,
            html,
        )

        if sent:
            # Mark as notified
            job_ids = [j["id"] for j in jobs]
            now = datetime.now(timezone.utc).isoformat()
            for jid in job_ids:
                sb.table("user_jobs").update({"notified_at": now}).eq("id", jid).execute()

            total_sent += 1
            logger.info(f"Sent digest to {email}: {len(jobs)} jobs")

    if total_sent:
        logger.info(f"Email notifications: sent {total_sent} digests")


def _build_digest_html(name: str, jobs: list[dict]) -> str:
    """Build a simple HTML email digest."""
    rows = ""
    for job in jobs:
        raw = job.get("raw_jobs", {})
        score = job.get("match_score", 0)
        priority = job.get("match_priority", "low")
        keywords = job.get("match_keywords", [])
        if isinstance(keywords, str):
            import json
            try:
                keywords = json.loads(keywords)
            except Exception:
                keywords = []

        badge_color = {"high": "#16a34a", "medium": "#ca8a04", "low": "#6b7280"}.get(priority, "#6b7280")

        rows += f"""
        <tr>
          <td style="padding:8px;text-align:center">
            <span style="background:{badge_color};color:white;padding:2px 8px;border-radius:12px;font-weight:bold">{score:.0f}</span>
          </td>
          <td style="padding:8px">
            <a href="{raw.get('source_url', '#')}" style="color:#2563eb;text-decoration:none;font-weight:600">{raw.get('title', 'N/A')}</a>
            <br><span style="color:#6b7280;font-size:13px">{raw.get('company', '')} — {raw.get('location', 'N/A')}</span>
          </td>
          <td style="padding:8px;font-size:12px;color:#6b7280">{', '.join(keywords[:5])}</td>
        </tr>"""

    return f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto">
      <h2 style="color:#1e40af">Hi {name},</h2>
      <p>Here are your latest job matches:</p>
      <table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:8px">
        <thead>
          <tr style="background:#f9fafb">
            <th style="padding:8px;text-align:center;width:60px">Score</th>
            <th style="padding:8px;text-align:left">Job</th>
            <th style="padding:8px;text-align:left">Keywords</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="margin-top:20px;font-size:13px;color:#9ca3af">
        — JobScout | <a href="#" style="color:#6b7280">Unsubscribe</a>
      </p>
    </div>"""


async def _send_email(api_key: str, from_email: str, to: str, subject: str, html: str) -> bool:
    """Send email via Resend API."""
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": from_email,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
            if resp.status_code in (200, 201):
                return True
            logger.error(f"Resend API error {resp.status_code}: {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False
