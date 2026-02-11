import asyncio
import json
import logging
import sqlite3

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from job_agent.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, load_config
from job_agent.storage import (
    get_companies,
    get_company_by_id,
    get_connection,
    get_job_by_id,
    get_jobs_to_notify,
    get_monthly_cost,
    get_stats,
    update_company_status,
    update_job_status,
)

logger = logging.getLogger(__name__)

# Reference to scheduler for pause/resume — set from scheduler.py
_scheduler_ref = None


def set_scheduler_ref(scheduler):
    global _scheduler_ref
    _scheduler_ref = scheduler


def build_application() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("companies", cmd_companies))
    app.add_handler(CommandHandler("costs", cmd_costs))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CallbackQueryHandler(handle_callback))
    return app


# --- Commands ---

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Job Agent actif.\n\n"
        "Commandes :\n"
        "/status — Stats globales\n"
        "/pending — Offres en attente\n"
        "/companies — Entreprises cibles\n"
        "/costs — Coûts LLM du mois\n"
        "/pause — Mettre en pause\n"
        "/resume — Reprendre"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    stats = get_stats(conn)
    conn.close()
    text = (
        f"Total offres : {stats['total']}\n"
        f"Nouvelles : {stats['new']}\n"
        f"Notifiées : {stats['notified']}\n"
        f"Intéressantes : {stats['interested']}\n"
        f"Postulé : {stats['applied']}\n"
        f"Rejetées : {stats['rejected']}\n"
        f"Coût LLM ce mois : ${stats['monthly_cost_usd']}"
    )
    await update.message.reply_text(text)


async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cfg = load_config()
    min_score = cfg["scoring"]["min_score_notify"]
    jobs = get_jobs_to_notify(conn, min_score)
    conn.close()

    if not jobs:
        await update.message.reply_text("Aucune offre en attente.")
        return

    for job in jobs[:10]:
        await _send_job_notification(update.message.chat_id, job, context.bot)


async def cmd_costs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cost = get_monthly_cost(conn)
    cfg = load_config()
    budget = cfg["llm"]["monthly_budget_usd"]
    conn.close()
    pct = (cost / budget * 100) if budget > 0 else 0
    await update.message.reply_text(
        f"Coût LLM ce mois : ${cost:.4f}\n"
        f"Budget : ${budget:.2f}\n"
        f"Utilisation : {pct:.1f}%"
    )


async def cmd_companies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    companies = get_companies(conn, status="pending")
    conn.close()

    if not companies:
        await update.message.reply_text("Aucune entreprise cible en attente.")
        return

    for company in companies[:10]:
        score = company.get("relevance_score") or 0
        text = (
            f"🏢 {company['name']}\n"
            f"📍 {company.get('location') or 'N/A'}\n"
            f"🔧 {company.get('sector') or 'N/A'}\n"
            f"⭐ Score: {score:.0f}\n"
            f"🔗 {company.get('website') or 'N/A'}"
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Préparer candidature", callback_data=f"prepare_{company['id']}"),
                InlineKeyboardButton("❌ Ignorer", callback_data=f"skipcompany_{company['id']}"),
            ],
        ])
        await update.message.reply_text(text, reply_markup=keyboard)


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _scheduler_ref:
        _scheduler_ref.pause()
        await update.message.reply_text("Scheduler en pause.")
    else:
        await update.message.reply_text("Scheduler non disponible.")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _scheduler_ref:
        _scheduler_ref.resume()
        await update.message.reply_text("Scheduler repris.")
    else:
        await update.message.reply_text("Scheduler non disponible.")


# --- Notifications ---

async def notify_new_jobs(bot: Bot, conn: sqlite3.Connection, max_notifications: int = 10) -> int:
    """Send notifications for high-scoring new jobs. Returns count sent."""
    cfg = load_config()
    min_score = cfg["scoring"]["min_score_notify"]
    jobs = get_jobs_to_notify(conn, min_score)

    if not jobs:
        return 0

    sent = 0
    for job in jobs[:max_notifications]:
        try:
            await _send_job_notification(int(TELEGRAM_CHAT_ID), job, bot)
            update_job_status(conn, job["id"], "notified")
            sent += 1
            await asyncio.sleep(1.5)
        except Exception as e:
            logger.error(f"Failed to notify job {job['id']}: {e}")
            if "Flood control" in str(e) or "Timed out" in str(e):
                await asyncio.sleep(30)

    return sent


async def _send_job_notification(chat_id: int, job: dict, bot: Bot):
    score = job.get("match_score", 0)
    priority = job.get("match_priority", "low").upper()

    match_kw = json.loads(job.get("match_keywords") or "[]")
    missing_kw = json.loads(job.get("missing_keywords") or "[]")
    reasoning = job.get("match_reasoning", "")

    salary = _format_salary_display(job)
    location = job.get("location") or "Non précisé"
    remote = job.get("remote_type", "unknown")
    remote_icon = {"full": "Full remote", "partial": "Hybride", "office": "Sur site"}.get(remote, "")

    text = (
        f"{'🔴' if priority == 'HIGH' else '🟡' if priority == 'MEDIUM' else '⚪'} "
        f"Score: {score:.0f}/100 — {priority}\n\n"
        f"📋 {job['title']}\n"
        f"🏢 {job['company']}\n"
        f"📍 {location}"
        f"{f' ({remote_icon})' if remote_icon else ''}\n"
        f"{f'💰 {salary}' if salary else ''}\n"
        f"🔗 {job['source'].upper()}\n\n"
    )

    if match_kw:
        text += f"✅ Match: {', '.join(match_kw[:8])}\n"
    if missing_kw:
        text += f"❌ Manque: {', '.join(missing_kw[:5])}\n"
    if reasoning:
        text += f"\n💡 {reasoning}\n"

    buttons = [
        [
            InlineKeyboardButton("🔍 Voir l'offre", url=job["source_url"]),
            InlineKeyboardButton("✅ Intéressé", callback_data=f"interested_{job['id']}"),
        ],
        [
            InlineKeyboardButton("❌ Ignorer", callback_data=f"reject_{job['id']}"),
            InlineKeyboardButton("⏸ Plus tard", callback_data=f"later_{job['id']}"),
        ],
    ]
    if score >= 70:
        buttons.append([
            InlineKeyboardButton("📝 Préparer candidature", callback_data=f"preparejob_{job['id']}"),
        ])
    keyboard = InlineKeyboardMarkup(buttons)

    await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)


# --- Callbacks ---

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_", 1)
    if len(parts) != 2:
        return

    action, id_str = parts
    try:
        item_id = int(id_str)
    except ValueError:
        return

    conn = get_connection()

    # Company actions
    if action == "prepare":
        company = get_company_by_id(conn, item_id)
        if not company:
            await query.edit_message_text("Entreprise introuvable.")
            conn.close()
            return
        update_company_status(conn, item_id, "prepared")
        await query.edit_message_text(
            f"📝 {company['name']} — candidature spontanée en préparation\n"
            f"🔗 {company.get('website') or 'N/A'}\n\n"
            f"Lancez `/resume-tailoring` dans Claude Code pour générer le CV sur mesure."
        )
        conn.close()
        return

    if action == "skipcompany":
        company = get_company_by_id(conn, item_id)
        if company:
            update_company_status(conn, item_id, "rejected")
            await query.edit_message_text(f"❌ {company['name']} — ignoré")
        conn.close()
        return

    if action == "preparejob":
        job = get_job_by_id(conn, item_id)
        if not job:
            await query.edit_message_text("Offre introuvable.")
            conn.close()
            return
        update_job_status(conn, item_id, "interested")
        await query.edit_message_text(
            f"📝 {job['title']} @ {job['company']} — candidature en préparation\n"
            f"🔗 {job['source_url']}\n\n"
            f"Lancez `/resume-tailoring` dans Claude Code pour générer le CV sur mesure."
        )
        conn.close()
        return

    # Job actions
    job = get_job_by_id(conn, item_id)
    if not job:
        await query.edit_message_text("Offre introuvable.")
        conn.close()
        return

    if action == "interested":
        update_job_status(conn, item_id, "interested")
        await query.edit_message_text(
            f"✅ {job['title']} @ {job['company']} — marqué comme intéressant\n"
            f"🔗 {job['source_url']}"
        )
    elif action == "reject":
        update_job_status(conn, item_id, "rejected")
        await query.edit_message_text(
            f"❌ {job['title']} @ {job['company']} — ignoré"
        )
    elif action == "later":
        await query.edit_message_text(
            f"⏸ {job['title']} @ {job['company']} — remis à plus tard\n"
            f"Utilisez /pending pour revoir les offres."
        )

    conn.close()


# --- Helpers ---

def _format_salary_display(job: dict) -> str:
    s_min = job.get("salary_min")
    s_max = job.get("salary_max")
    currency = job.get("salary_currency", "EUR")
    if s_min and s_max:
        if s_min >= 1000:
            return f"{s_min // 1000}K-{s_max // 1000}K {currency}"
        return f"{s_min}-{s_max} {currency}"
    if s_min:
        return f"{s_min // 1000}K+ {currency}" if s_min >= 1000 else f"{s_min}+ {currency}"
    return ""
