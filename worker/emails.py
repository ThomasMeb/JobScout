"""Transactional emails via Brevo API — welcome, weekly digest, application confirmation."""
import logging
from datetime import datetime, timedelta, timezone

import httpx

from worker.config import get_settings
from worker.db import get_supabase

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


async def _send_brevo_email(to_email: str, to_name: str, subject: str, html: str) -> bool:
    """Send an email via Brevo transactional API."""
    settings = get_settings()
    if not settings.brevo_api_key:
        logger.debug("Brevo API key not configured, skipping email")
        return False

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(
                BREVO_API_URL,
                headers={
                    "api-key": settings.brevo_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "sender": {"name": "JobScout", "email": settings.notification_from_email.split("<")[-1].rstrip(">") if "<" in settings.notification_from_email else "noreply@mebarki.dev"},
                    "to": [{"email": to_email, "name": to_name}],
                    "subject": subject,
                    "htmlContent": html,
                },
            )
            if resp.status_code in (200, 201):
                return True
            logger.error(f"Brevo API error {resp.status_code}: {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False


# ---------------------------------------------------------------------------
# Welcome email
# ---------------------------------------------------------------------------

def _build_welcome_html(name: str) -> str:
    return f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:560px;margin:0 auto;padding:20px">
      <h1 style="color:#1e40af;font-size:24px">Bienvenue sur JobScout{f', {name}' if name else ''} !</h1>
      <p>Votre profil est configuré. Voici ce qui va se passer :</p>
      <ol style="line-height:1.8">
        <li><strong>Scraping automatique</strong> — 9 sources scannées toutes les 4h</li>
        <li><strong>Scoring IA</strong> — chaque offre est notée selon votre CV</li>
        <li><strong>Notifications</strong> — top 10 des offres score &ge; 80, &lt; 48h</li>
        <li><strong>Candidature auto</strong> — CV adapté + lettre en 1 clic</li>
      </ol>
      <p>Consultez votre <a href="https://jobscout.mebarki.dev/dashboard" style="color:#2563eb">dashboard</a> pour suivre les offres.</p>
      <p style="margin-top:24px;color:#6b7280;font-size:13px">— L'équipe JobScout</p>
    </div>"""


async def send_welcome_email(user_id: str) -> bool:
    """Send welcome email to a newly onboarded user."""
    sb = get_supabase()
    profile = (
        sb.table("profiles")
        .select("name, notification_email, welcome_email_sent_at")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not profile.data:
        return False

    if profile.data.get("welcome_email_sent_at"):
        return False

    email = profile.data.get("notification_email")
    name = profile.data.get("name") or ""
    if not email:
        return False

    html = _build_welcome_html(name)
    sent = await _send_brevo_email(email, name, "Bienvenue sur JobScout !", html)
    if sent:
        sb.table("profiles").update({
            "welcome_email_sent_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user_id).execute()
        logger.info(f"Welcome email sent to {user_id[:8]}")
    return sent


async def send_pending_welcome_emails():
    """Send welcome emails to all users who haven't received one yet."""
    sb = get_supabase()
    profiles = (
        sb.table("profiles")
        .select("id")
        .eq("onboarding_completed", True)
        .is_("welcome_email_sent_at", "null")
        .execute()
    )
    for user in (profiles.data or []):
        await send_welcome_email(user["id"])


# ---------------------------------------------------------------------------
# Weekly digest
# ---------------------------------------------------------------------------

def _build_weekly_digest_html(name: str, jobs: list[dict]) -> str:
    rows = ""
    for job in jobs[:5]:
        raw = job.get("raw_jobs") or {}
        score = job.get("match_score", 0)
        title = raw.get("title", "N/A")
        company = raw.get("company", "")
        url = raw.get("source_url", "#")
        location = raw.get("location") or "N/A"
        badge = "#16a34a" if score >= 80 else "#ca8a04" if score >= 60 else "#6b7280"

        rows += f"""
        <tr>
          <td style="padding:8px;text-align:center">
            <span style="background:{badge};color:white;padding:2px 10px;border-radius:12px;font-weight:bold;font-size:14px">{score:.0f}</span>
          </td>
          <td style="padding:8px">
            <a href="{url}" style="color:#2563eb;text-decoration:none;font-weight:600">{title}</a>
            <br><span style="color:#6b7280;font-size:13px">{company} — {location}</span>
          </td>
        </tr>"""

    return f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:560px;margin:0 auto;padding:20px">
      <h2 style="color:#1e40af">Votre résumé hebdomadaire{f', {name}' if name else ''}</h2>
      <p>Voici le top {len(jobs)} des offres de la semaine :</p>
      <table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:8px">
        <tbody>{rows}</tbody>
      </table>
      <p style="margin-top:16px">
        <a href="https://jobscout.mebarki.dev/dashboard" style="display:inline-block;background:#2563eb;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600">
          Voir toutes les offres
        </a>
      </p>
      <p style="margin-top:24px;color:#6b7280;font-size:13px">— JobScout</p>
    </div>"""


async def send_weekly_digest(user_id: str) -> bool:
    """Send weekly top-5 digest email to a user."""
    sb = get_supabase()
    profile = (
        sb.table("profiles")
        .select("name, notification_email, last_digest_at, min_score_notify")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not profile.data:
        return False

    email = profile.data.get("notification_email")
    name = profile.data.get("name") or ""
    if not email:
        return False

    # Check if digest already sent this week
    last_digest = profile.data.get("last_digest_at")
    if last_digest:
        last_dt = datetime.fromisoformat(last_digest.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - last_dt < timedelta(days=7):
            return False

    min_score = profile.data.get("min_score_notify") or 70
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    jobs = (
        sb.table("user_jobs")
        .select("match_score, raw_jobs(title, company, location, source_url)")
        .eq("user_id", user_id)
        .gte("match_score", min_score)
        .gte("scored_at", week_ago)
        .order("match_score", desc=True)
        .limit(5)
        .execute()
    )

    if not jobs.data:
        return False

    html = _build_weekly_digest_html(name, jobs.data)
    sent = await _send_brevo_email(
        email, name,
        f"JobScout : top {len(jobs.data)} offres de la semaine",
        html,
    )
    if sent:
        sb.table("profiles").update({
            "last_digest_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user_id).execute()
        logger.info(f"Weekly digest sent to {user_id[:8]}")
    return sent


async def send_weekly_digests_all_users():
    """Send weekly digests to all eligible users."""
    sb = get_supabase()
    settings = get_settings()
    if not settings.brevo_api_key:
        return

    profiles = (
        sb.table("profiles")
        .select("id")
        .eq("onboarding_completed", True)
        .execute()
    )
    count = 0
    for user in (profiles.data or []):
        if await send_weekly_digest(user["id"]):
            count += 1
    if count:
        logger.info(f"Weekly digest: sent to {count} users")


# ---------------------------------------------------------------------------
# Application confirmation
# ---------------------------------------------------------------------------

def _build_confirmation_html(name: str, job_title: str, company: str, to_email: str) -> str:
    return f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:560px;margin:0 auto;padding:20px">
      <h2 style="color:#16a34a">Candidature envoyée !</h2>
      <p>Bonjour{f' {name}' if name else ''},</p>
      <p>Votre candidature pour <strong>{job_title}</strong> chez <strong>{company}</strong> a été envoyée automatiquement à <code>{to_email}</code>.</p>
      <ul style="line-height:1.8">
        <li>CV adapté au poste</li>
        <li>Lettre de motivation personnalisée</li>
      </ul>
      <p>Suivez l'avancement dans votre <a href="https://jobscout.mebarki.dev/dashboard" style="color:#2563eb">dashboard</a>.</p>
      <p style="margin-top:24px;color:#6b7280;font-size:13px">— JobScout</p>
    </div>"""


async def send_application_confirmation(user_id: str, job_title: str, company: str, sent_to: str) -> bool:
    """Send confirmation email after auto-apply."""
    sb = get_supabase()
    profile = (
        sb.table("profiles")
        .select("name, notification_email")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not profile.data:
        return False

    email = profile.data.get("notification_email")
    name = profile.data.get("name") or ""
    if not email:
        return False

    html = _build_confirmation_html(name, job_title, company, sent_to)
    return await _send_brevo_email(
        email, name,
        f"Candidature envoyée — {job_title} @ {company}",
        html,
    )
