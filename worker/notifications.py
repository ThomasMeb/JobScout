"""Notifications for scored jobs — email (Resend) and Telegram (interactive bot)."""
import json
import logging
from datetime import datetime, timezone

import httpx

from worker.config import get_settings
from worker.db import get_supabase

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


async def send_notifications():
    """Send digests to users with new unnotified high-score jobs (email + Telegram)."""
    settings = get_settings()

    has_email = bool(settings.resend_api_key)
    has_telegram = bool(settings.telegram_bot_token)

    if not has_email and not has_telegram:
        logger.info("No notification channels configured, skipping")
        return

    sb = get_supabase()

    profiles = (
        sb.table("profiles")
        .select("id, name, notification_email, telegram_chat_id, min_score_notify")
        .eq("onboarding_completed", True)
        .execute()
    )

    if not profiles.data:
        return

    total_email = 0
    total_telegram = 0

    for user in profiles.data:
        user_id = user["id"]
        email = user.get("notification_email")
        chat_id = user.get("telegram_chat_id")

        if not email and not chat_id:
            continue

        min_score = user.get("min_score_notify") or 70

        new_jobs = (
            sb.table("user_jobs")
            .select("id, match_score, match_priority, match_keywords, missing_keywords, match_reasoning, "
                    "raw_jobs(title, company, location, remote_type, salary_min, salary_max, "
                    "salary_currency, source, source_url, apply_url)")
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

        name = user.get("name") or "there"
        sent = False

        # Email
        if email and has_email:
            html = _build_digest_html(name, jobs)
            subject = f"JobScout: {len(jobs)} new job{'s' if len(jobs) > 1 else ''} matching your profile"
            if await _send_email(settings.resend_api_key, settings.notification_from_email, email, subject, html):
                total_email += 1
                sent = True

        # Telegram — use interactive bot if available, otherwise fallback to simple API
        if chat_id and has_telegram:
            bot = _get_telegram_bot()
            if bot:
                from worker.telegram_bot import send_interactive_notifications
                count = await send_interactive_notifications(user_id, chat_id, jobs, bot)
                if count > 0:
                    total_telegram += 1
                    sent = True
            else:
                text = _build_telegram_message(name, jobs)
                if await _send_telegram(settings.telegram_bot_token, chat_id, text):
                    total_telegram += 1
                    sent = True

        if sent:
            job_ids = [j["id"] for j in jobs]
            now = datetime.now(timezone.utc).isoformat()
            for jid in job_ids:
                sb.table("user_jobs").update({"notified_at": now}).eq("id", jid).execute()
            logger.info(f"Notified user {user_id[:8]}...: {len(jobs)} jobs")

    if total_email or total_telegram:
        logger.info(f"Notifications sent: {total_email} emails, {total_telegram} telegram")


def _get_telegram_bot():
    """Try to get the running bot instance."""
    try:
        from worker.telegram_bot import get_bot
        return get_bot()
    except Exception as e:
        logger.warning(f"Failed to get Telegram bot instance: {e}")
        return None


def _build_digest_html(name: str, jobs: list[dict]) -> str:
    """Build a simple HTML email digest."""
    rows = ""
    for job in jobs:
        raw = job.get("raw_jobs", {})
        score = job.get("match_score", 0)
        priority = job.get("match_priority", "low")
        keywords = job.get("match_keywords", [])
        if isinstance(keywords, str):
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


def _build_telegram_message(name: str, jobs: list[dict]) -> str:
    """Build a Telegram digest message with Markdown (fallback when bot not running)."""
    lines = [f"*Hi {name}, {len(jobs)} new job{'s' if len(jobs) > 1 else ''}:*\n"]
    for job in jobs[:10]:
        raw = job.get("raw_jobs", {})
        score = job.get("match_score", 0)
        title = raw.get("title", "N/A")
        company = raw.get("company", "")
        url = raw.get("source_url", "")
        priority = job.get("match_priority", "low")
        emoji = {"high": "🟢", "medium": "🟡", "low": "⚪"}.get(priority, "⚪")
        link = f"[{title}]({url})" if url else title
        lines.append(f"{emoji} *{score:.0f}* — {link}\n_{company}_")

    if len(jobs) > 10:
        lines.append(f"\n_...and {len(jobs) - 10} more_")

    return "\n".join(lines)


async def _send_telegram(bot_token: str, chat_id: str, text: str) -> bool:
    """Send message via Telegram Bot API (simple fallback)."""
    url = TELEGRAM_API_URL.format(token=bot_token)
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                },
            )
            if resp.status_code == 200:
                return True
            logger.error(f"Telegram API error {resp.status_code}: {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Failed to send Telegram to {chat_id}: {e}")
            return False


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
