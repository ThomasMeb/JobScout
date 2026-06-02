"""Notifications for scored jobs — email (Resend) and Telegram (interactive bot)."""
import json
import logging
import re
from datetime import datetime, timezone

import httpx

from worker.config import get_settings
from worker.db import get_supabase

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

# Telegram hard limit on message text is 4096 chars; leave headroom for emojis
# and trailing footer added on truncation.
TELEGRAM_MAX_TEXT = 3900

# Markdown V1 special chars that break parsing if unbalanced inside literal
# text. We escape them on every user-supplied field before interpolating.
_MD_ESCAPE_RE = re.compile(r"([_*\[\]`])")


def _md_escape(text: object) -> str:
    """Escape Telegram Markdown V1 special chars in user-supplied content.

    Without this, a job title like "Senior Dev (C++)" or a company "A_B_C"
    breaks Telegram's parser and the API returns 400 — the user receives
    nothing for that whole digest.
    """
    if text is None:
        return ""
    return _MD_ESCAPE_RE.sub(r"\\\1", str(text))


async def send_notifications():
    """Send digests to users with new unnotified high-score jobs (email + Telegram).

    Every "nothing sent" path is logged with an explicit reason, so a silent
    weeks-long outage can be diagnosed from the logs alone instead of guessing.
    """
    settings = get_settings()

    has_email = bool(settings.resend_api_key)
    has_telegram = bool(settings.telegram_bot_token)

    if not has_email and not has_telegram:
        logger.warning("No notification channels configured (RESEND_API_KEY and TELEGRAM_BOT_TOKEN both empty), skipping")
        return

    sb = get_supabase()

    profiles = (
        sb.table("profiles")
        .select("id, name, notification_email, telegram_chat_id, min_score_notify")
        .eq("onboarding_completed", True)
        .execute()
    )

    if not profiles.data:
        logger.info("No onboarded users to notify")
        return

    total_email = 0
    total_telegram = 0
    failed_sends = 0

    for user in profiles.data:
        user_id = user["id"]
        email = user.get("notification_email")
        chat_id = user.get("telegram_chat_id")

        if not email and not chat_id:
            logger.info(f"User {user_id[:8]}...: no notification channel (email/telegram_chat_id both unset), skipping")
            continue

        min_score = user.get("min_score_notify") or 70
        max_notif = settings.max_notifications_per_cycle

        new_jobs = (
            sb.table("user_jobs")
            .select("id, match_score, match_priority, match_keywords, missing_keywords, match_reasoning, "
                    "raw_jobs(title, company, location, remote_type, salary_min, salary_max, "
                    "salary_currency, source, source_url, apply_url, posted_at)")
            .eq("user_id", user_id)
            .gte("match_score", min_score)
            .is_("notified_at", "null")
            .order("match_score", desc=True)
            .limit(max_notif)
            .execute()
        )

        jobs = new_jobs.data or []

        if not jobs:
            # Distinguish "scoring produced nothing" from "threshold too high"
            # so the user knows whether to lower min_score_notify.
            try:
                below = (
                    sb.table("user_jobs")
                    .select("id", count="exact")
                    .eq("user_id", user_id)
                    .lt("match_score", min_score)
                    .is_("notified_at", "null")
                    .limit(0)
                    .execute()
                )
                below_count = below.count or 0
            except Exception:
                below_count = -1
            if below_count > 0:
                logger.info(
                    f"User {user_id[:8]}...: 0 jobs ≥ threshold {min_score}, but "
                    f"{below_count} unnotified jobs below it — consider lowering min_score_notify"
                )
            else:
                logger.info(f"User {user_id[:8]}...: no new unnotified jobs ≥ {min_score}")
            continue

        name = user.get("name") or ""
        sent = False

        # Email
        if email and has_email:
            html = _build_digest_html(name, jobs)
            subject = f"JobScout : {len(jobs)} nouvelle{'s' if len(jobs) > 1 else ''} offre{'s' if len(jobs) > 1 else ''} correspondant à votre profil"
            if await _send_email(settings.resend_api_key, settings.notification_from_email, email, subject, html):
                total_email += 1
                sent = True

        # Telegram — digest enrichi + bouton par offre pour détails interactifs
        if chat_id and has_telegram:
            text = _build_digest_text(name, jobs)
            keyboard = _build_digest_keyboard(jobs)
            if await _send_telegram(settings.telegram_bot_token, chat_id, text, reply_markup=keyboard):
                total_telegram += 1
                sent = True

        if sent:
            job_ids = [j["id"] for j in jobs]
            now = datetime.now(timezone.utc).isoformat()
            for jid in job_ids:
                sb.table("user_jobs").update({"notified_at": now}).eq("id", jid).execute()
            logger.info(f"Notified user {user_id[:8]}...: {len(jobs)} jobs")
        else:
            # Critical: jobs matched but delivery failed on every channel.
            # notified_at stays null so they're retried next cycle, but we
            # must surface this — it's the silent-outage signature.
            failed_sends += 1
            logger.error(
                f"User {user_id[:8]}...: {len(jobs)} jobs matched but ALL delivery "
                f"channels failed (email={bool(email and has_email)}, "
                f"telegram={bool(chat_id and has_telegram)}) — will retry next cycle"
            )

    if total_email or total_telegram:
        logger.info(f"Notifications sent: {total_email} emails, {total_telegram} telegram")
    if failed_sends:
        logger.error(f"Notifications: {failed_sends} user(s) had matching jobs but delivery failed")


def _format_salary(raw: dict) -> str:
    """Format salary range for display."""
    s_min = raw.get("salary_min")
    s_max = raw.get("salary_max")
    currency = raw.get("salary_currency", "EUR")
    if s_min and s_max:
        return f"{s_min // 1000}K-{s_max // 1000}K {currency}" if s_min >= 1000 else f"{s_min}-{s_max} {currency}"
    if s_min:
        return f"{s_min // 1000}K+ {currency}" if s_min >= 1000 else f"{s_min}+ {currency}"
    return ""


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
      <h2 style="color:#1e40af">Bonjour{f' {name}' if name else ''},</h2>
      <p>Voici vos dernières offres correspondantes :</p>
      <table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:8px">
        <thead>
          <tr style="background:#f9fafb">
            <th style="padding:8px;text-align:center;width:60px">Score</th>
            <th style="padding:8px;text-align:left">Offre</th>
            <th style="padding:8px;text-align:left">Mots-clés</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="margin-top:20px;font-size:13px;color:#9ca3af">
        — JobScout | <a href="#" style="color:#6b7280">Se désabonner</a>
      </p>
    </div>"""


def _parse_keywords(value) -> list[str]:
    """Parse keywords from string or list."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return []
    return []


def _build_digest_text(name: str, jobs: list[dict]) -> str:
    """Build an enriched digest message listing all jobs with details.

    All user-supplied fields are escaped for Markdown V1 to avoid 400 parse
    errors that would silently drop the entire digest.
    """
    greeting_name = _md_escape(name) if name else ""
    greeting = f"📬 *{greeting_name}, " if greeting_name else "📬 *"
    lines = [f"{greeting}{len(jobs)} nouvelle{'s' if len(jobs) > 1 else ''} offre{'s' if len(jobs) > 1 else ''}*"]
    for job in jobs:
        raw = job.get("raw_jobs") or {}
        score = job.get("match_score") or 0
        priority = (job.get("match_priority") or "low").lower()
        emoji = {"high": "🔴", "medium": "🟡", "low": "⚪"}.get(priority, "⚪")
        salary = _format_salary(raw)
        location = raw.get("location") or ""
        remote = raw.get("remote_type") or ""
        remote_label = {"full": "🏠 Télétravail", "partial": "🔀 Hybride", "office": "🏢 Sur site"}.get(remote, "")
        match_kw = _parse_keywords(job.get("match_keywords"))
        missing_kw = _parse_keywords(job.get("missing_keywords"))
        source_url = raw.get("source_url") or ""

        title = _md_escape(raw.get("title") or "N/A")
        # A safe Markdown link requires no ')' in the URL; fall back to plain
        # text otherwise — better a clean message than a parse failure.
        if source_url and ")" not in source_url and "(" not in source_url:
            link = f"[{title}]({source_url})"
        else:
            link = title

        company = _md_escape(raw.get("company") or "N/A")
        block = f"{emoji} *{score:.0f}/100* — {link}"
        block += f"\n🏢 {company}"
        meta = []
        if location:
            meta.append(f"📍 {_md_escape(location)}")
        if remote_label:
            meta.append(remote_label)
        if salary:
            meta.append(f"💰 {_md_escape(salary)}")
        if meta:
            block += f"\n{' · '.join(meta)}"
        if match_kw:
            block += f"\n✅ {_md_escape(', '.join(match_kw[:6]))}"
        if missing_kw:
            block += f"\n❌ {_md_escape(', '.join(missing_kw[:4]))}"

        lines.append(block)

    lines.append("⬇️ _Clique sur une offre pour interagir_")
    text = "\n\n".join(lines)
    if len(text) > TELEGRAM_MAX_TEXT:
        text = text[:TELEGRAM_MAX_TEXT].rstrip() + "\n\n…"
    return text


def _build_digest_keyboard(jobs: list[dict]) -> dict:
    """Build inline keyboard with detail button + link per job."""
    buttons = []
    for job in jobs:
        raw = job.get("raw_jobs", {})
        score = job.get("match_score", 0)
        priority = (job.get("match_priority") or "low").lower()
        emoji = {"high": "🔴", "medium": "🟡", "low": "⚪"}.get(priority, "⚪")
        title = raw.get("title", "N/A")
        if len(title) > 30:
            title = title[:27] + "..."
        label = f"{emoji} {score:.0f} — {title}"
        source_url = raw.get("source_url", "")
        row = [{"text": label, "callback_data": f"detail_{job['id']}"}]
        if source_url:
            row.append({"text": "🔗", "url": source_url})
        buttons.append(row)
    return {"inline_keyboard": buttons}


def _strip_markdown(text: str) -> str:
    """Remove Markdown V1 syntax for the plain-text fallback.

    Drops [link](url) → "link" and unescaped *bold* / _italic_ / `code`
    markers, while preserving the literal characters that were backslash-
    escaped by _md_escape.
    """
    # [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Protect backslash-escaped literals via private-use placeholders, so the
    # next step doesn't strip them as if they were Markdown syntax.
    placeholders = {"\\_": "\x00U", "\\*": "\x00S", "\\[": "\x00L", "\\]": "\x00R", "\\`": "\x00B"}
    for esc, ph in placeholders.items():
        text = text.replace(esc, ph)
    # Now drop genuine Markdown markers.
    text = re.sub(r"[*_`]", "", text)
    # Restore the literals.
    for esc, ph in placeholders.items():
        text = text.replace(ph, esc[1])
    return text


async def _send_telegram(bot_token: str, chat_id: str, text: str, reply_markup: dict | None = None) -> bool:
    """Send a Telegram message with Markdown, falling back to plain text on parse failure.

    Returns True iff the message was actually delivered. Detailed error context
    (status, body, message length) is logged so operators can find the broken
    field instead of seeing a silent failure.
    """
    url = TELEGRAM_API_URL.format(token=bot_token)
    async with httpx.AsyncClient(timeout=15) as client:
        for attempt, parse_mode in enumerate(["Markdown", None]):
            try:
                payload: dict = {
                    "chat_id": chat_id,
                    "text": text if parse_mode else _strip_markdown(text),
                    "disable_web_page_preview": True,
                }
                if parse_mode:
                    payload["parse_mode"] = parse_mode
                if reply_markup:
                    payload["reply_markup"] = json.dumps(reply_markup)

                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    if attempt > 0:
                        logger.warning(
                            f"Telegram delivered to {chat_id} only after Markdown→plain fallback. "
                            f"Inspect digest content for unescaped chars."
                        )
                    return True

                # 400 → almost always a Markdown parse error. Retry without parse_mode.
                if resp.status_code == 400 and parse_mode == "Markdown":
                    logger.warning(
                        f"Telegram 400 (likely Markdown parse) for {chat_id}, "
                        f"len={len(text)}, body={resp.text[:300]}, falling back to plain text"
                    )
                    continue

                logger.error(
                    f"Telegram API error {resp.status_code} for {chat_id} "
                    f"(parse_mode={parse_mode}, len={len(text)}): {resp.text[:300]}"
                )
                return False
            except Exception as e:
                logger.error(f"Failed to send Telegram to {chat_id} (parse_mode={parse_mode}): {e}")
                return False
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
