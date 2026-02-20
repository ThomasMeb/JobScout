import argparse
import asyncio
import logging

from rich.logging import RichHandler

from job_agent.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from job_agent.notifier import build_application, set_scheduler_ref
from job_agent.scheduler import JobScheduler, run_cycle
from job_agent.storage import init_db


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


async def run_once():
    """Run a single scrape-score-notify cycle."""
    init_db()
    await run_cycle()


async def run_daemon():
    """Run scheduler + Telegram bot concurrently."""
    init_db()
    scheduler = JobScheduler()

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        set_scheduler_ref(scheduler)
        app = build_application()

        # Run both scheduler and telegram bot
        async with app:
            await app.start()
            # Run first cycle immediately
            try:
                await run_cycle()
            except Exception as e:
                logging.error(f"Initial cycle failed: {e}")

            await app.updater.start_polling()
            logging.info("Telegram bot started. Waiting for commands...")

            # Run scheduler loop
            try:
                await scheduler.start()
            except asyncio.CancelledError:
                pass
            finally:
                await app.updater.stop()
                await app.stop()
    else:
        logging.warning("Telegram not configured — running scheduler only")
        await run_cycle()
        await scheduler.start()


def main():
    parser = argparse.ArgumentParser(description="Job Search Agent")
    parser.add_argument("--once", action="store_true", help="Run one cycle then exit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.once:
        asyncio.run(run_once())
    else:
        asyncio.run(run_daemon())


if __name__ == "__main__":
    main()
