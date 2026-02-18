"""JobScout SaaS Worker — scrape global + score per-user loop."""
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
    """One full worker cycle: scrape → score → notify."""
    logger.info("Worker cycle starting...")
    try:
        await scrape_global()
        await score_per_user()
        await send_notifications()
        logger.info("Worker cycle complete")
    except Exception as e:
        logger.error(f"Worker cycle failed: {e}", exc_info=True)


async def main():
    settings = get_settings()
    interval = settings.cycle_interval_hours
    logger.info(f"Worker starting — cycle every {interval}h")

    # Run first cycle immediately
    await run_cycle()

    # Loop
    while True:
        await asyncio.sleep(interval * 3600)
        await run_cycle()


if __name__ == "__main__":
    asyncio.run(main())
