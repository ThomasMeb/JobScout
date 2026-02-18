"""JobScout SaaS Worker — scrape global + score per-user loop."""
import asyncio
import logging

from worker.tasks import scrape_global, score_per_user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

CYCLE_INTERVAL_HOURS = 4


async def run_cycle():
    """One full worker cycle: scrape then score."""
    logger.info("Worker cycle starting...")
    try:
        await scrape_global()
        await score_per_user()
        logger.info("Worker cycle complete")
    except Exception as e:
        logger.error(f"Worker cycle failed: {e}", exc_info=True)


async def main():
    logger.info(f"Worker starting — cycle every {CYCLE_INTERVAL_HOURS}h")

    # Run first cycle immediately
    await run_cycle()

    # Loop
    while True:
        await asyncio.sleep(CYCLE_INTERVAL_HOURS * 3600)
        await run_cycle()


if __name__ == "__main__":
    asyncio.run(main())
