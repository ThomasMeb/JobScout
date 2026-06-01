"""End-to-end notification pipeline diagnostic.

Run against production to find exactly where the "no Telegram jobs" pipeline
breaks. Read-only except for the optional --test-telegram live ping.

Usage:
    python -m worker.diagnose                 # full report, all users
    python -m worker.diagnose --user <uuid>   # focus one user
    python -m worker.diagnose --test-telegram # also send a live test message

The pipeline it walks, in order:
    worker heartbeat → scrape_runs → raw_jobs → per-user profile config →
    user_jobs scored → pending notifications → LLM budget → Telegram reachability
"""
import argparse
import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from worker.config import get_settings
from worker.db import get_supabase, get_user_monthly_cost

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def _h(title: str):
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def _age(iso: str | None) -> str:
    if not iso:
        return "never"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        hours = delta.total_seconds() / 3600
        if hours < 1:
            return f"{delta.total_seconds() / 60:.0f} min ago"
        if hours < 48:
            return f"{hours:.1f}h ago"
        return f"{hours / 24:.1f} days ago"
    except Exception:
        return iso


def check_worker(sb) -> None:
    _h("1. WORKER HEARTBEAT")
    try:
        hb = sb.table("worker_heartbeats").select("*").eq("id", "main").maybe_single().execute()
        if not hb.data:
            print("❌ No heartbeat row — worker has likely NEVER run successfully.")
            return
        d = hb.data
        status = d.get("status")
        updated = d.get("updated_at")
        last_cycle = d.get("last_cycle_at")
        print(f"   status        : {status}")
        print(f"   cycles        : {d.get('cycle_count')}")
        print(f"   updated       : {_age(updated)}")
        print(f"   last cycle    : {_age(last_cycle)}")
        if d.get("error_message"):
            print(f"   ⚠️ error       : {d['error_message']}")
        # Verdict
        try:
            age_h = (datetime.now(timezone.utc) - datetime.fromisoformat(updated.replace("Z", "+00:00"))).total_seconds() / 3600
            if age_h > 8:
                print(f"   ❌ VERDICT: heartbeat is {age_h:.0f}h stale — worker is DOWN or stuck.")
            elif status in ("crashed", "error"):
                print(f"   ❌ VERDICT: worker reports status={status}.")
            else:
                print("   ✅ Worker appears alive.")
        except Exception:
            pass
    except Exception as e:
        print(f"❌ Could not read worker_heartbeats: {e}")


def check_scraping(sb) -> None:
    _h("2. SCRAPING (last 24h)")
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    try:
        runs = (
            sb.table("scrape_runs")
            .select("source, status, jobs_found, jobs_new, started_at")
            .gte("started_at", cutoff)
            .order("started_at", desc=True)
            .execute()
        )
        rows = runs.data or []
        if not rows:
            print("   ⚠️ No scrape runs in the last 24h — scraping may be stopped.")
            return
        by_source: dict[str, dict] = {}
        for r in rows:
            s = r["source"]
            agg = by_source.setdefault(s, {"runs": 0, "found": 0, "new": 0, "last_status": r["status"]})
            agg["runs"] += 1
            agg["found"] += r.get("jobs_found") or 0
            agg["new"] += r.get("jobs_new") or 0
        for source, agg in sorted(by_source.items()):
            flag = "✅" if agg["found"] else "⚠️"
            print(f"   {flag} {source:14s}: {agg['runs']} runs, {agg['found']} found, {agg['new']} new (last: {agg['last_status']})")
        total_new = sum(a["new"] for a in by_source.values())
        if total_new == 0:
            print("   ❌ VERDICT: 0 new jobs scraped in 24h — pipeline starves here.")
        else:
            print(f"   ✅ {total_new} new jobs entered the pool in 24h.")
    except Exception as e:
        print(f"❌ Could not read scrape_runs: {e}")


def check_raw_jobs(sb) -> None:
    _h("3. RAW JOBS POOL")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    try:
        recent = sb.table("raw_jobs").select("id", count="exact").gte("scraped_at", cutoff).limit(0).execute()
        total = sb.table("raw_jobs").select("id", count="exact").limit(0).execute()
        print(f"   total raw_jobs      : {total.count}")
        print(f"   scraped last 7 days : {recent.count}")
        if (recent.count or 0) == 0:
            print("   ❌ VERDICT: no fresh jobs in 7 days — scoring has nothing to work on.")
        else:
            print("   ✅ Fresh jobs available for scoring.")
    except Exception as e:
        print(f"❌ Could not read raw_jobs: {e}")


def check_user(sb, settings, user: dict) -> None:
    user_id = user["id"]
    name = user.get("name") or "(no name)"
    _h(f"4. USER {name} [{user_id[:8]}...]")

    chat_id = user.get("telegram_chat_id")
    min_score = user.get("min_score_notify") or 70
    onboarded = user.get("onboarding_completed")
    budget = float(user.get("monthly_budget_usd") or 5.0)

    print(f"   onboarding_completed : {onboarded}  {'✅' if onboarded else '❌ (excluded from scoring AND notifications!)'}")
    print(f"   telegram_chat_id     : {chat_id or '❌ NOT SET'}")
    print(f"   notification_email   : {user.get('notification_email') or '(none)'}")
    print(f"   min_score_notify     : {min_score}  {'⚠️ very high' if min_score >= 80 else ''}")
    print(f"   plan                 : {user.get('plan') or 'free'}")

    # Budget
    try:
        cost = get_user_monthly_cost(sb, user_id)
        flag = "❌ EXHAUSTED" if cost >= budget else "✅"
        print(f"   LLM cost this month  : ${cost:.4f} / ${budget:.2f}  {flag}")
    except Exception as e:
        print(f"   LLM cost             : error {e}")

    # Scoring activity
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    try:
        scored = sb.table("user_jobs").select("match_score").eq("user_id", user_id).gte("created_at", cutoff).execute()
        scores = [r["match_score"] for r in (scored.data or []) if r.get("match_score") is not None]
        print(f"   jobs scored (7d)     : {len(scores)}")
        if scores:
            above = sum(1 for s in scores if s >= min_score)
            print(f"     score range        : {min(scores):.0f}–{max(scores):.0f} (avg {sum(scores)/len(scores):.0f})")
            print(f"     ≥ threshold {min_score:<3.0f}    : {above}  {'❌ none reach threshold' if above == 0 else '✅'}")
        elif len(scores) == 0:
            print("     ❌ VERDICT: scoring produced 0 jobs in 7 days (budget? LLM key? no matches?).")
    except Exception as e:
        print(f"   scoring check        : error {e}")

    # Pending notifications
    try:
        pending = (
            sb.table("user_jobs")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .gte("match_score", min_score)
            .is_("notified_at", "null")
            .limit(0)
            .execute()
        )
        pcount = pending.count or 0
        print(f"   PENDING notifications: {pcount}")
        if pcount > 0:
            print(f"     ⚠️ {pcount} jobs ≥ {min_score} waiting to be sent. If you receive nothing,")
            print("       delivery is failing → run: python -m worker.flush_notifications")
        else:
            print("     (nothing queued above threshold right now)")
    except Exception as e:
        print(f"   pending check        : error {e}")


async def test_telegram(settings, chat_id: str) -> None:
    _h("5. LIVE TELEGRAM TEST")
    if not settings.telegram_bot_token:
        print("   ❌ TELEGRAM_BOT_TOKEN not configured.")
        return
    # First verify the token itself.
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            me = await client.get(f"https://api.telegram.org/bot{settings.telegram_bot_token}/getMe")
            if me.status_code != 200:
                print(f"   ❌ Bot token invalid/revoked (getMe → {me.status_code}: {me.text[:200]})")
                return
            print(f"   ✅ Bot token valid: @{me.json().get('result', {}).get('username')}")
        except Exception as e:
            print(f"   ❌ getMe failed: {e}")
            return
        # Then send a real message.
        try:
            resp = await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": "✅ JobScout diagnostic: la livraison Telegram fonctionne."},
            )
            if resp.status_code == 200:
                print(f"   ✅ Test message delivered to chat_id {chat_id}.")
            else:
                print(f"   ❌ sendMessage → {resp.status_code}: {resp.text[:200]}")
                print("      (chat_id wrong, or you never pressed /start on the bot)")
        except Exception as e:
            print(f"   ❌ sendMessage failed: {e}")


async def main():
    parser = argparse.ArgumentParser(description="Diagnose the JobScout notification pipeline")
    parser.add_argument("--user", help="Focus a single user UUID")
    parser.add_argument("--test-telegram", action="store_true", help="Send a live Telegram test message")
    args = parser.parse_args()

    settings = get_settings()
    sb = get_supabase()

    check_worker(sb)
    check_scraping(sb)
    check_raw_jobs(sb)

    q = sb.table("profiles").select(
        "id, name, telegram_chat_id, notification_email, min_score_notify, "
        "onboarding_completed, monthly_budget_usd, plan"
    )
    if args.user:
        q = q.eq("id", args.user)
    profiles = q.execute()

    if not profiles.data:
        print("\n❌ No matching profiles found.")
        return

    for user in profiles.data:
        check_user(sb, settings, user)
        if args.test_telegram and user.get("telegram_chat_id"):
            await test_telegram(settings, user["telegram_chat_id"])

    _h("DONE")
    print("Follow the ❌ markers above — the first one is the root cause.")


if __name__ == "__main__":
    asyncio.run(main())
