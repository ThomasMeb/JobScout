"""One-time script to flush pending unnotified jobs accumulated during the outage.

Usage: python -m worker.flush_notifications

Sends a catch-up digest with top 20 jobs per user, then marks ALL pending as notified.
"""
import asyncio
import logging
from datetime import datetime, timezone

from worker.config import get_settings
from worker.db import get_supabase
from worker.notifications import _send_telegram

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def flush():
    sb = get_supabase()
    settings = get_settings()

    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not configured, aborting")
        return

    profiles = (
        sb.table("profiles")
        .select("id, name, telegram_chat_id, min_score_notify")
        .eq("onboarding_completed", True)
        .not_.is_("telegram_chat_id", "null")
        .execute()
    )

    for user in (profiles.data or []):
        user_id = user["id"]
        chat_id = user.get("telegram_chat_id")
        if not chat_id:
            continue

        min_score = user.get("min_score_notify") or 70
        name = user.get("name") or ""

        all_pending = (
            sb.table("user_jobs")
            .select("id, match_score, match_priority, "
                    "raw_jobs(title, company, location, source_url)")
            .eq("user_id", user_id)
            .gte("match_score", min_score)
            .is_("notified_at", "null")
            .order("match_score", desc=True)
            .execute()
        )

        jobs = all_pending.data or []
        if not jobs:
            logger.info(f"User {user_id[:8]}...: no pending notifications")
            continue

        total = len(jobs)
        top_jobs = jobs[:20]

        greeting = f"*{name}*, " if name else ""
        lines = [f"📬 {greeting}rattrapage : *{total} offres* accumulées\n"
                 f"Voici le top {len(top_jobs)} :"]

        for j in top_jobs:
            raw = j.get("raw_jobs") or {}
            score = j.get("match_score", 0)
            title = raw.get("title", "N/A")
            company = raw.get("company", "N/A")
            url = raw.get("source_url", "")
            link = f"[{title}]({url})" if url else title
            lines.append(f"• *{score:.0f}* — {link}\n  🏢 {company}")

        if total > 20:
            lines.append(f"\n_{total - 20} autres offres marquées comme lues._")

        text = "\n".join(lines)
        sent = await _send_telegram(settings.telegram_bot_token, chat_id, text)

        if sent:
            now = datetime.now(timezone.utc).isoformat()
            for j in jobs:
                sb.table("user_jobs").update({"notified_at": now}).eq("id", j["id"]).execute()
            logger.info(f"Flushed {total} notifications for user {user_id[:8]}... ({name})")
        else:
            logger.error(f"Failed to send Telegram to user {user_id[:8]}...")

        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(flush())
