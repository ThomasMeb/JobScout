"""JobScout SaaS Worker — scrape global + score per-user + notifications + Phase 2 modules."""
import asyncio
import logging
import traceback
from datetime import datetime, timezone

import httpx
import sentry_sdk

from worker.config import get_settings
from worker.notifications import send_notifications
from worker.tasks import scrape_global, score_per_user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def _send_crash_alert(message: str):
    """Send a Telegram alert on critical worker failure (direct API call)."""
    settings = get_settings()
    if not settings.telegram_bot_token:
        return
    try:
        from worker.db import get_supabase
        sb = get_supabase()
        profiles = sb.table("profiles").select("telegram_chat_id").not_.is_("telegram_chat_id", "null").execute()
        for p in profiles.data or []:
            chat_id = p.get("telegram_chat_id")
            if chat_id:
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(
                        f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                        json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
                    )
    except Exception as e:
        logger.error(f"Failed to send crash alert: {e}")


async def _update_heartbeat(status: str, cycle_count: int = 0, error_message: str | None = None):
    """Update worker heartbeat in Supabase."""
    try:
        from worker.db import get_supabase
        sb = get_supabase()
        row = {
            "id": "main",
            "status": status,
            "cycle_count": cycle_count,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if status == "running":
            row["last_cycle_at"] = datetime.now(timezone.utc).isoformat()
        if error_message:
            row["error_message"] = error_message[:500]
        sb.table("worker_heartbeats").upsert(row).execute()
    except Exception as e:
        logger.warning(f"Failed to update heartbeat: {e}")


async def run_cycle(cycle_count: int) -> int:
    """One full worker cycle: scrape → score → notify → company research → notion sync."""
    logger.info("Worker cycle starting...")
    try:
        await scrape_global()
        await score_per_user()
        await send_notifications()

        # Phase 2: Company research
        try:
            from worker.company_research import run_company_research_all_users
            await run_company_research_all_users()
        except Exception as e:
            logger.error(f"Company research failed: {e}", exc_info=True)

        # Phase 2: Notion sync
        try:
            from worker.notion_sync import sync_all_users
            await sync_all_users()
        except Exception as e:
            logger.error(f"Notion sync failed: {e}", exc_info=True)

        cycle_count += 1
        await _update_heartbeat("running", cycle_count)
        logger.info(f"Worker cycle #{cycle_count} complete")
        return cycle_count
    except Exception as e:
        logger.error(f"Worker cycle failed: {e}", exc_info=True)
        sentry_sdk.capture_exception(e)
        await _update_heartbeat("error", cycle_count, str(e))
        return cycle_count


async def main():
    settings = get_settings()

    # Init Sentry (no-op if DSN is empty)
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=0.2,
            environment=getattr(settings, "environment", "production"),
        )
        logger.info("Sentry initialized for worker")

    interval = settings.cycle_interval_hours
    logger.info(f"Worker starting — cycle every {interval}h")

    # Startup health check: verify Supabase connection
    try:
        from worker.db import get_supabase
        sb = get_supabase()
        sb.table("profiles").select("id").limit(1).execute()
        logger.info("Supabase connection OK")
    except Exception as e:
        logger.critical(f"Supabase connection failed at startup: {e}")
        raise SystemExit(1)

    await _update_heartbeat("starting")

    # Start Telegram bot in background (if configured)
    if settings.telegram_bot_token:
        try:
            from worker.telegram_bot import start_bot
            asyncio.create_task(start_bot())
            logger.info("Telegram bot task created")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")

    # Run cycles
    cycle_count = 0
    try:
        cycle_count = await run_cycle(cycle_count)
        while True:
            await asyncio.sleep(interval * 3600)
            cycle_count = await run_cycle(cycle_count)
    except Exception as e:
        error_tb = traceback.format_exc()
        logger.critical(f"Worker crashed: {e}\n{error_tb}")
        sentry_sdk.capture_exception(e)
        await _update_heartbeat("crashed", cycle_count, str(e))
        await _send_crash_alert(
            f"🚨 <b>JobScout Worker CRASHED</b>\n\n"
            f"<code>{str(e)[:300]}</code>\n\n"
            f"Cycles completed: {cycle_count}"
        )
        raise


if __name__ == "__main__":
    asyncio.run(main())
