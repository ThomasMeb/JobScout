import argparse
import asyncio
import contextlib
import logging
import signal

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
    # Prevent secret leakage: httpx logs full request URLs at INFO level, which
    # include the Telegram bot token (https://api.telegram.org/bot<TOKEN>/...).
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


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

            # Graceful shutdown: handle SIGTERM (Docker stop) and SIGINT so the
            # scheduler/bot stop cleanly instead of being SIGKILLed (exit 137).
            loop = asyncio.get_running_loop()
            stop_event = asyncio.Event()
            for sig in (signal.SIGTERM, signal.SIGINT):
                with contextlib.suppress(NotImplementedError):
                    loop.add_signal_handler(sig, stop_event.set)

            sched_task = asyncio.create_task(scheduler.start())
            stop_task = asyncio.create_task(stop_event.wait())
            try:
                await asyncio.wait(
                    {sched_task, stop_task}, return_when=asyncio.FIRST_COMPLETED
                )
            finally:
                for task in (sched_task, stop_task):
                    task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await task
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
