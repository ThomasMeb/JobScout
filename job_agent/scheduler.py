import asyncio
import logging
from datetime import datetime

from telegram import Bot

from job_agent.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, load_config
from job_agent.company_research import run_company_research
from job_agent.llm import check_deepseek_balance
from job_agent.matcher import score_new_jobs
from job_agent.notion_sync import sync_companies_to_notion, sync_jobs_to_notion
from job_agent.notifier import notify_new_jobs
from job_agent.scrapers.adzuna import AdzunaScraper
from job_agent.scrapers.apec import APECScraper
from job_agent.scrapers.base import RawJob
from job_agent.scrapers.francetravail import FranceTravailScraper
from job_agent.scrapers.freework import FreeWorkScraper
from job_agent.scrapers.hellowork import HelloWorkScraper
from job_agent.scrapers.indeed_rss import IndeedRSSScraper
from job_agent.scrapers.jobspy import JobSpyScraper
from job_agent.scrapers.remoteok import RemoteOKScraper
from job_agent.scrapers.welovedevs import WeLoveDevsScraper
from job_agent.scrapers.wttj import WTTJScraper
from job_agent.storage import get_connection, init_db, insert_job, log_scrape_run

logger = logging.getLogger(__name__)

ALL_SCRAPERS = [
    ("wttj", WTTJScraper()),
    ("remoteok", RemoteOKScraper()),
    ("adzuna", AdzunaScraper()),
    ("indeed_rss", IndeedRSSScraper()),
    ("francetravail", FranceTravailScraper()),
    ("jobspy", JobSpyScraper()),
    ("hellowork", HelloWorkScraper()),
    ("apec", APECScraper()),
    ("freework", FreeWorkScraper()),
    ("welovedevs", WeLoveDevsScraper()),
]


async def run_cycle():
    """Execute one full scrape → score → notify cycle."""
    cfg = load_config()
    init_db()
    conn = get_connection()

    # Check DeepSeek balance (alert only, never blocks scoring)
    balance_info = await check_deepseek_balance()
    if balance_info:
        threshold = cfg["llm"].get("balance_alert_threshold_usd", 2.0)
        balance = balance_info["total_balance"]
        currency = balance_info["currency"]
        logger.info(f"DeepSeek balance: {balance:.2f} {currency}")
        if balance < threshold:
            logger.warning(f"DeepSeek balance low: {balance:.2f} {currency} (threshold: {threshold:.2f})")
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                bot = Bot(token=TELEGRAM_BOT_TOKEN)
                await bot.send_message(
                    chat_id=int(TELEGRAM_CHAT_ID),
                    text=f"⚠️ Solde DeepSeek bas : {balance:.2f} {currency}\nPense à recharger !",
                )
    else:
        logger.warning("Could not check DeepSeek balance")

    queries = cfg["search"]["queries"]
    locations = cfg["search"]["locations"]

    # 1. Scrape all sources
    total_found = 0
    total_new = 0

    for source_key, scraper in ALL_SCRAPERS:
        source_cfg = cfg["sources"].get(source_key, {})
        if not source_cfg.get("enabled", True):
            continue

        logger.info(f"Scraping {source_key}...")
        try:
            raw_jobs: list[RawJob] = await scraper.scrape(queries, locations, source_cfg)
            found = len(raw_jobs)
            new = 0

            for rj in raw_jobs:
                job_id = insert_job(
                    conn,
                    title=rj.title,
                    company=rj.company,
                    location=rj.location,
                    remote_type=rj.remote_type,
                    salary_min=rj.salary_min,
                    salary_max=rj.salary_max,
                    salary_currency=rj.salary_currency,
                    description=rj.description,
                    tags=rj.tags,
                    source=rj.source,
                    source_url=rj.source_url,
                    apply_url=rj.apply_url,
                    company_url=rj.company_url,
                    posted_at=rj.posted_at.isoformat() if rj.posted_at else None,
                )
                if job_id is not None:
                    new += 1

            log_scrape_run(conn, source_key, found, new)
            total_found += found
            total_new += new
            logger.info(f"  {source_key}: {found} found, {new} new")

        except Exception as e:
            logger.error(f"Scraper {source_key} failed: {e}")
            log_scrape_run(conn, source_key, 0, 0, status="error", error_message=str(e))

    logger.info(f"Total: {total_found} found, {total_new} new")

    # 2. Score new jobs
    if total_new > 0:
        scored = await score_new_jobs(conn)
        logger.info(f"Scored {scored} jobs")

    # 3. Company research
    try:
        new_companies = await run_company_research(conn, cfg)
        if new_companies:
            logger.info(f"Company research: {new_companies} new companies")
    except Exception as e:
        logger.error(f"Company research failed: {e}")

    # 4. Notify via Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        max_notifs = cfg["telegram"]["max_notifications_per_run"]
        sent = await notify_new_jobs(bot, conn, max_notifs)
        logger.info(f"Sent {sent} notifications")

        if total_new == 0 and not cfg["telegram"]["silent_if_no_new"]:
            await bot.send_message(
                chat_id=int(TELEGRAM_CHAT_ID),
                text="📭 Aucune nouvelle offre trouvée.",
            )

    # 5. Sync to Notion
    notion_cfg = cfg.get("notion", {})
    if notion_cfg.get("enabled", False):
        try:
            min_score_sync = notion_cfg.get("min_score_sync", 50)
            synced_jobs = sync_jobs_to_notion(conn, min_score_sync)
            if synced_jobs:
                logger.info(f"Notion: synced {synced_jobs} jobs")
            if notion_cfg.get("sync_companies", False):
                synced_companies = sync_companies_to_notion(conn)
                if synced_companies:
                    logger.info(f"Notion: synced {synced_companies} companies")
        except Exception as e:
            logger.error(f"Notion sync failed: {e}")

    conn.close()
    logger.info("Cycle complete")


class JobScheduler:
    def __init__(self):
        self._running = True
        self._task = None

    async def start(self):
        cfg = load_config()
        interval = cfg["scheduler"]["scrape_interval_hours"]
        active_hours = cfg["scheduler"]["active_hours"]
        logger.info(f"Scheduler started: every {interval}h, active {active_hours[0]}h-{active_hours[1]}h")

        while True:
            now = datetime.now()
            if self._running and active_hours[0] <= now.hour < active_hours[1]:
                try:
                    await run_cycle()
                except Exception as e:
                    logger.error(f"Cycle failed: {e}")

            # Sleep until next cycle
            await asyncio.sleep(interval * 3600)

    def pause(self):
        self._running = False
        logger.info("Scheduler paused")

    def resume(self):
        self._running = True
        logger.info("Scheduler resumed")
