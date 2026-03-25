"""JobScout SaaS Worker — scrape global + score per-user + notifications + Phase 2 modules."""
import asyncio
import json
import logging
import traceback
from datetime import datetime, timezone

import httpx
import sentry_sdk

from worker.config import get_settings
from worker.notifications import send_notifications
from worker.tasks import scrape_global, score_per_user


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
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
        row["error_message"] = error_message[:500] if error_message else None
        sb.table("worker_heartbeats").upsert(row).execute()
    except Exception as e:
        logger.warning(f"Failed to update heartbeat: {e}")


async def run_scrape_cycle():
    """Tier 1: Scrape global + generate embeddings."""
    logger.info("Scrape cycle starting...")
    try:
        await scrape_global()  # includes embed_new_jobs()
    except Exception as e:
        logger.error(f"Scrape cycle failed: {e}", exc_info=True)
        sentry_sdk.capture_exception(e)


async def run_score_cycle(cycle_count: int) -> int:
    """Tier 2+3: Score per user + downstream tasks (notifications, sync, emails)."""
    logger.info("Score cycle starting...")
    try:
        try:
            await score_per_user()
        except Exception as e:
            logger.error(f"Scoring failed: {e}", exc_info=True)
            sentry_sdk.capture_exception(e)

        # Always attempt notifications, even if scoring failed
        # (there may be previously scored but unnotified jobs)
        await send_notifications()

        # Phase 2: Company research
        try:
            from worker.company_research import run_company_research_all_users
            await run_company_research_all_users()
        except Exception as e:
            logger.error(f"Company research failed: {e}", exc_info=True)

        # Phase 2: Notion sync (push DB → Notion)
        try:
            from worker.notion_sync import sync_all_users
            await sync_all_users()
        except Exception as e:
            logger.error(f"Notion push sync failed: {e}", exc_info=True)

        # Phase 6: Notion pull (Notion → DB)
        try:
            from worker.notion_sync import pull_all_users
            await pull_all_users()
        except Exception as e:
            logger.error(f"Notion pull sync failed: {e}", exc_info=True)

        # Phase 9: Transactional emails (welcome + weekly digest)
        try:
            from worker.emails import send_pending_welcome_emails, send_weekly_digests_all_users
            await send_pending_welcome_emails()
            await send_weekly_digests_all_users()
        except Exception as e:
            logger.error(f"Transactional emails failed: {e}", exc_info=True)

        cycle_count += 1
        await _update_heartbeat("running", cycle_count)
        logger.info(f"Score cycle #{cycle_count} complete")
        return cycle_count
    except Exception as e:
        logger.error(f"Score cycle failed: {e}", exc_info=True)
        sentry_sdk.capture_exception(e)
        await _update_heartbeat("error", cycle_count, str(e))
        return cycle_count


async def run_full_cycle(cycle_count: int) -> int:
    """Full cycle: scrape + score + downstream (used for first cycle)."""
    await run_scrape_cycle()
    return await run_score_cycle(cycle_count)


async def _validate_schema(settings):
    """Check expected DB schema at startup. Logs warnings but does NOT block."""
    from worker.db import get_supabase
    sb = get_supabase()
    warnings = []

    # Core tables
    for table in ["profiles", "raw_jobs", "user_jobs", "llm_usage", "scrape_runs"]:
        try:
            sb.table(table).select("*", count="exact").limit(0).execute()
        except Exception:
            warnings.append(f"CRITICAL: table '{table}' missing")

    # Embedding infrastructure (only if enabled)
    if settings.embeddings_enabled:
        try:
            sb.table("profiles").select("embedding_threshold").limit(1).execute()
        except Exception:
            warnings.append("profiles.embedding_threshold column missing (migration 013)")
        for tbl in ["job_embeddings", "user_embeddings"]:
            try:
                sb.table(tbl).select("*", count="exact").limit(0).execute()
            except Exception:
                warnings.append(f"table '{tbl}' missing (migration 013)")

    if warnings:
        for w in warnings:
            logger.warning(f"Schema check: {w}")
        critical = [w for w in warnings if "CRITICAL" in w]
        if critical:
            await _send_crash_alert(
                "⚠️ <b>JobScout Schema Warning</b>\n\n"
                + "\n".join(f"• {w}" for w in warnings)
            )
    else:
        logger.info("Schema validation OK")


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

    logger.info(
        f"Worker starting — scrape every {settings.scrape_interval_hours}h, "
        f"score every {settings.scoring_interval_hours}h"
    )

    # Startup health check: verify Supabase connection
    try:
        from worker.db import get_supabase
        sb = get_supabase()
        sb.table("profiles").select("id").limit(1).execute()
        logger.info("Supabase connection OK")
    except Exception as e:
        logger.critical(f"Supabase connection failed at startup: {e}")
        raise SystemExit(1)

    # Schema validation: detect missing tables/columns early
    await _validate_schema(settings)

    await _update_heartbeat("starting")

    # Start Telegram bot in background (if configured)
    if settings.telegram_bot_token:
        try:
            from worker.telegram_bot import start_bot
            asyncio.create_task(start_bot())
            logger.info("Telegram bot task created")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")

    # Run first full cycle, then decouple scrape/score loops
    cycle_count = 0
    try:
        cycle_count = await run_full_cycle(cycle_count)

        async def scrape_loop():
            while True:
                await asyncio.sleep(settings.scrape_interval_hours * 3600)
                await run_scrape_cycle()

        async def score_loop():
            nonlocal cycle_count
            while True:
                await asyncio.sleep(settings.scoring_interval_hours * 3600)
                cycle_count = await run_score_cycle(cycle_count)

        await asyncio.gather(scrape_loop(), score_loop())
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
    finally:
        # Cleanup Playwright browser if it was used
        try:
            from job_agent.scrapers.browser import close_browser
            await close_browser()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
