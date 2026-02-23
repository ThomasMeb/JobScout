"""JobScout SaaS Worker — scrape global + score per-user + notifications + Phase 2 modules."""
import asyncio
import logging

from worker.config import get_settings
from worker.notifications import send_notifications
from worker.tasks import scrape_global, score_per_user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

async def run_cycle():
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

        logger.info("Worker cycle complete")
    except Exception as e:
        logger.error(f"Worker cycle failed: {e}", exc_info=True)


async def main():
    settings = get_settings()
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

    # Start Telegram bot in background (if configured)
    if settings.telegram_bot_token:
        try:
            from worker.telegram_bot import start_bot
            asyncio.create_task(start_bot())
            logger.info("Telegram bot task created")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")

    # Run first cycle immediately
    await run_cycle()

    # Loop
    while True:
        await asyncio.sleep(interval * 3600)
        await run_cycle()


if __name__ == "__main__":
    asyncio.run(main())
