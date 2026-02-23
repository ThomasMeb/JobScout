"""Telegram bot interactif — commandes, notifications enrichies, pipeline candidature.

Adapted from legacy/job_agent/notifier.py for multi-tenant SaaS (Supabase).
Multi-tenant: identifies user by telegram_chat_id in profiles.
"""

import asyncio
import io
import json
import logging
from datetime import datetime, timezone

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from worker.config import get_settings
from worker.db import get_supabase

logger = logging.getLogger(__name__)

# Global application reference
_app: Application | None = None


def _get_user_id(chat_id: int | str) -> str | None:
    """Lookup user_id from telegram_chat_id."""
    sb = get_supabase()
    result = (
        sb.table("profiles")
        .select("id")
        .eq("telegram_chat_id", str(chat_id))
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["id"]
    return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "JobScout actif.\n\n"
        "Commandes :\n"
        "/status — Stats globales\n"
        "/pending — Offres en attente\n"
        "/companies — Entreprises cibles\n"
        "/costs — Coûts LLM du mois\n"
        "/preferences — Préférences apprises\n"
        "/prepare <id> — Préparer candidature\n"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = _get_user_id(update.message.chat_id)
    if not user_id:
        await update.message.reply_text("Compte non lié. Configurez votre chat_id dans le dashboard.")
        return

    sb = get_supabase()

    total = sb.table("user_jobs").select("id", count="exact").eq("user_id", user_id).execute()
    new = sb.table("user_jobs").select("id", count="exact").eq("user_id", user_id).eq("status", "new").execute()
    interested = sb.table("user_jobs").select("id", count="exact").eq("user_id", user_id).eq("status", "interested").execute()
    applied = sb.table("user_jobs").select("id", count="exact").eq("user_id", user_id).eq("status", "applied").execute()
    rejected = sb.table("user_jobs").select("id", count="exact").eq("user_id", user_id).eq("status", "rejected").execute()

    monthly_cost = _get_monthly_cost(sb, user_id)

    text = (
        f"Total offres : {total.count or 0}\n"
        f"Nouvelles : {new.count or 0}\n"
        f"Intéressantes : {interested.count or 0}\n"
        f"Postulé : {applied.count or 0}\n"
        f"Rejetées : {rejected.count or 0}\n"
        f"Coût LLM ce mois : ${monthly_cost:.4f}"
    )
    await update.message.reply_text(text)


async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = _get_user_id(update.message.chat_id)
    if not user_id:
        await update.message.reply_text("Compte non lié.")
        return

    sb = get_supabase()
    profile = sb.table("profiles").select("min_score_notify").eq("id", user_id).single().execute()
    min_score = (profile.data or {}).get("min_score_notify") or 70

    jobs = (
        sb.table("user_jobs")
        .select("id, match_score, match_priority, match_keywords, missing_keywords, match_reasoning, "
                "raw_jobs(title, company, location, remote_type, salary_min, salary_max, salary_currency, source, source_url, apply_url)")
        .eq("user_id", user_id)
        .in_("status", ["new", "notified"])
        .gte("match_score", min_score)
        .order("match_score", desc=True)
        .limit(10)
        .execute()
    )

    if not jobs.data:
        await update.message.reply_text("Aucune offre en attente.")
        return

    for job in jobs.data:
        await _send_job_notification(update.message.chat_id, job, context.bot)
        await asyncio.sleep(0.5)


async def cmd_costs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = _get_user_id(update.message.chat_id)
    if not user_id:
        await update.message.reply_text("Compte non lié.")
        return

    sb = get_supabase()
    monthly_cost = _get_monthly_cost(sb, user_id)

    profile = sb.table("profiles").select("monthly_budget_usd").eq("id", user_id).single().execute()
    budget = float((profile.data or {}).get("monthly_budget_usd") or 5.0)
    remaining = max(0, budget - monthly_cost)

    await update.message.reply_text(
        f"Coût LLM ce mois : ${monthly_cost:.4f}\n"
        f"Budget mensuel : ${budget:.2f}\n"
        f"Restant : ${remaining:.4f}"
    )


async def cmd_companies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = _get_user_id(update.message.chat_id)
    if not user_id:
        await update.message.reply_text("Compte non lié.")
        return

    sb = get_supabase()
    companies = (
        sb.table("companies")
        .select("id, name, location, sector, website, relevance_score")
        .eq("user_id", user_id)
        .eq("spontaneous_status", "pending")
        .order("relevance_score", desc=True)
        .limit(10)
        .execute()
    )

    if not companies.data:
        await update.message.reply_text("Aucune entreprise cible en attente.")
        return

    for company in companies.data:
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
                InlineKeyboardButton("📝 Préparer", callback_data=f"preparecompany_{company['id']}"),
                InlineKeyboardButton("❌ Ignorer", callback_data=f"skipcompany_{company['id']}"),
            ],
        ])
        await update.message.reply_text(text, reply_markup=keyboard)
        await asyncio.sleep(0.3)


async def cmd_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = _get_user_id(update.message.chat_id)
    if not user_id:
        await update.message.reply_text("Compte non lié.")
        return

    from worker.feedback_loop import analyze_keyword_preferences, get_feedback_stats

    stats = get_feedback_stats(user_id)
    prefs = analyze_keyword_preferences(user_id)

    text = (
        f"Feedback total : {stats['total_feedback']}\n"
        f"  Intéressé : {stats['interested']}\n"
        f"  Rejeté : {stats['rejected']}\n"
        f"  Postulé : {stats['applied']}\n\n"
    )

    if stats["total_feedback"] < 5:
        text += "Pas assez de feedback (min 5) pour apprendre les préférences."
        await update.message.reply_text(text)
        return

    if prefs["preferred_keywords"]:
        kws = ", ".join(kw for kw, _ in prefs["preferred_keywords"][:10])
        text += f"Keywords préférés : {kws}\n\n"

    if prefs["avoided_keywords"]:
        kws = ", ".join(kw for kw, _ in prefs["avoided_keywords"][:10])
        text += f"Keywords évités : {kws}\n\n"

    if prefs["preferred_companies"]:
        companies = ", ".join(f"{c} ({n})" for c, n in prefs["preferred_companies"][:5])
        text += f"Entreprises : {companies}\n\n"

    if prefs["preferred_locations"]:
        locs = ", ".join(f"{loc} ({n})" for loc, n in prefs["preferred_locations"][:5])
        text += f"Localisations : {locs}\n"

    await update.message.reply_text(text)


async def cmd_prepare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = _get_user_id(update.message.chat_id)
    if not user_id:
        await update.message.reply_text("Compte non lié.")
        return

    if not context.args:
        await update.message.reply_text("Usage : /prepare <user_job_id>")
        return

    try:
        user_job_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID invalide. Usage : /prepare <user_job_id>")
        return

    sb = get_supabase()
    uj = (
        sb.table("user_jobs")
        .select("id, raw_jobs(title, company)")
        .eq("id", user_job_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not uj.data:
        await update.message.reply_text(f"Job #{user_job_id} introuvable.")
        return

    raw = uj.data.get("raw_jobs", {})
    await update.message.reply_text(
        f"Préparation en cours pour :\n"
        f"{raw.get('title', '?')} @ {raw.get('company', '?')}..."
    )

    asyncio.create_task(
        _run_candidature_pipeline(user_id, user_job_id, update.message.chat_id, context.bot)
    )


# ---------------------------------------------------------------------------
# Notifications enrichies
# ---------------------------------------------------------------------------

async def send_interactive_notifications(user_id: str, chat_id: str, jobs: list, bot: Bot) -> int:
    """Send individual job notifications with inline buttons. Returns count sent."""
    sent = 0
    for job in jobs:
        try:
            await _send_job_notification(int(chat_id), job, bot)
            sent += 1
            await asyncio.sleep(1.0)
        except Exception as e:
            logger.error(f"Failed to notify job {job.get('id')}: {e}")
            if "Flood control" in str(e) or "Timed out" in str(e):
                await asyncio.sleep(30)
    return sent


async def _send_job_notification(chat_id: int, job: dict, bot: Bot):
    raw = job.get("raw_jobs", {})
    score = job.get("match_score", 0)
    priority = (job.get("match_priority") or "low").upper()

    match_kw = job.get("match_keywords") or []
    if isinstance(match_kw, str):
        match_kw = json.loads(match_kw)
    missing_kw = job.get("missing_keywords") or []
    if isinstance(missing_kw, str):
        missing_kw = json.loads(missing_kw)
    reasoning = job.get("match_reasoning", "")

    salary = _format_salary_display(raw)
    location = raw.get("location") or "Non précisé"
    remote = raw.get("remote_type", "unknown")
    remote_icon = {"full": "Full remote", "partial": "Hybride", "office": "Sur site"}.get(remote, "")

    text = (
        f"{'🔴' if priority == 'HIGH' else '🟡' if priority == 'MEDIUM' else '⚪'} "
        f"Score: {score:.0f}/100 — {priority}\n\n"
        f"📋 {raw.get('title', 'N/A')}\n"
        f"🏢 {raw.get('company', '')}\n"
        f"📍 {location}"
        f"{f' ({remote_icon})' if remote_icon else ''}\n"
        f"{f'💰 {salary}' if salary else ''}\n"
        f"🔗 {raw.get('source', '').upper()}\n\n"
    )

    if match_kw:
        text += f"✅ Match: {', '.join(match_kw[:8])}\n"
    if missing_kw:
        text += f"❌ Manque: {', '.join(missing_kw[:5])}\n"
    if reasoning:
        text += f"\n💡 {reasoning}\n"

    job_id = job["id"]
    source_url = raw.get("source_url", "")

    buttons = [
        [
            InlineKeyboardButton("🔍 Voir", url=source_url) if source_url else InlineKeyboardButton("🔍 N/A", callback_data="noop"),
            InlineKeyboardButton("✅ Intéressé", callback_data=f"interested_{job_id}"),
        ],
        [
            InlineKeyboardButton("❌ Ignorer", callback_data=f"reject_{job_id}"),
            InlineKeyboardButton("⏸ Plus tard", callback_data=f"later_{job_id}"),
        ],
    ]
    if score >= 70:
        buttons.append([
            InlineKeyboardButton("📝 Préparer candidature", callback_data=f"preparejob_{job_id}"),
        ])
    keyboard = InlineKeyboardMarkup(buttons)

    await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)


# ---------------------------------------------------------------------------
# Candidature pipeline via Telegram
# ---------------------------------------------------------------------------

async def _run_candidature_pipeline(user_id: str, user_job_id: int, chat_id: int, bot: Bot):
    from worker.candidature import prepare_candidature

    try:
        result = await prepare_candidature(user_id, user_job_id)

        if result["status"] == "error":
            await bot.send_message(chat_id=chat_id, text="Erreur lors de la préparation.")
            return

        # Send CV PDF
        if result["cv_pdf_bytes"]:
            sb = get_supabase()
            uj = (
                sb.table("user_jobs")
                .select("raw_jobs(title, company, source_url, apply_url)")
                .eq("id", user_job_id)
                .single()
                .execute()
            )
            raw = (uj.data or {}).get("raw_jobs", {})
            title = raw.get("title", "job")[:30]
            company = raw.get("company", "company")

            pdf_io = io.BytesIO(result["cv_pdf_bytes"])
            pdf_io.name = f"CV_{company}_{title}.pdf"
            await bot.send_document(
                chat_id=chat_id,
                document=pdf_io,
                caption=f"CV adapté pour {title} @ {company}",
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text="PDF non généré (pdflatex manquant ?). Texte disponible ci-dessous.",
            )

        # Send cover letter
        if result["cover_letter"]:
            cover = result["cover_letter"]
            if len(cover) > 4000:
                cover = cover[:4000] + "\n..."
            await bot.send_message(chat_id=chat_id, text=f"📧 Lettre de motivation :\n\n{cover}")

        # Send LinkedIn tips
        if result["linkedin_tips"]:
            tips = result["linkedin_tips"]
            if len(tips) > 4000:
                tips = tips[:4000] + "\n..."
            await bot.send_message(chat_id=chat_id, text=f"🔗 Tips LinkedIn :\n\n{tips}")

        # Final buttons
        buttons = [
            [
                InlineKeyboardButton("✅ Valider", callback_data=f"validate_{user_job_id}"),
                InlineKeyboardButton("🔄 Régénérer", callback_data=f"regen_{user_job_id}"),
            ],
        ]

        sb = get_supabase()
        uj = (
            sb.table("user_jobs")
            .select("raw_jobs(apply_url, source_url)")
            .eq("id", user_job_id)
            .single()
            .execute()
        )
        raw = (uj.data or {}).get("raw_jobs", {})
        apply_url = raw.get("apply_url") or raw.get("source_url")
        if apply_url:
            buttons.append([InlineKeyboardButton("🔗 Postuler", url=apply_url)])

        await bot.send_message(
            chat_id=chat_id,
            text=f"Candidature prête — coût : ${result['total_cost']:.4f}",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        logger.error(f"Candidature pipeline failed for user_job {user_job_id}: {e}", exc_info=True)
        await bot.send_message(chat_id=chat_id, text=f"Erreur lors de la préparation : {e}")


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "noop":
        return

    parts = data.split("_", 1)
    if len(parts) != 2:
        return

    action, id_str = parts
    try:
        item_id = int(id_str)
    except ValueError:
        return

    user_id = _get_user_id(query.message.chat_id)
    if not user_id:
        await query.edit_message_text("Compte non lié.")
        return

    sb = get_supabase()

    # Company actions
    if action == "preparecompany":
        company = sb.table("companies").select("name, website").eq("id", item_id).eq("user_id", user_id).single().execute()
        if not company.data:
            await query.edit_message_text("Entreprise introuvable.")
            return
        sb.table("companies").update({"spontaneous_status": "prepared"}).eq("id", item_id).execute()
        await query.edit_message_text(
            f"📝 {company.data['name']} — candidature spontanée en préparation"
        )
        return

    if action == "skipcompany":
        company = sb.table("companies").select("name").eq("id", item_id).eq("user_id", user_id).single().execute()
        if company.data:
            sb.table("companies").update({"spontaneous_status": "rejected"}).eq("id", item_id).execute()
            await query.edit_message_text(f"❌ {company.data['name']} — ignoré")
        return

    # Job actions — fetch job info
    uj = (
        sb.table("user_jobs")
        .select("id, raw_jobs(title, company, source_url)")
        .eq("id", item_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not uj.data:
        await query.edit_message_text("Offre introuvable.")
        return

    raw = uj.data.get("raw_jobs", {})
    title = raw.get("title", "?")
    company = raw.get("company", "?")

    if action == "interested":
        sb.table("user_jobs").update({"status": "interested"}).eq("id", item_id).execute()
        await query.edit_message_text(
            f"✅ {title} @ {company} — marqué comme intéressant\n"
            f"🔗 {raw.get('source_url', '')}"
        )

    elif action == "reject":
        sb.table("user_jobs").update({"status": "rejected"}).eq("id", item_id).execute()
        await query.edit_message_text(f"❌ {title} @ {company} — ignoré")

    elif action == "later":
        await query.edit_message_text(
            f"⏸ {title} @ {company} — remis à plus tard\n"
            f"Utilisez /pending pour revoir les offres."
        )

    elif action == "preparejob":
        sb.table("user_jobs").update({"status": "interested"}).eq("id", item_id).execute()
        await query.edit_message_text(f"📝 {title} @ {company} — préparation en cours...")
        asyncio.create_task(
            _run_candidature_pipeline(user_id, item_id, query.message.chat_id, context.bot)
        )

    elif action == "validate":
        sb.table("user_jobs").update({"status": "applied"}).eq("id", item_id).execute()
        sb.table("applications").update({
            "status": "validated",
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("user_job_id", item_id).eq("status", "draft").execute()
        await query.edit_message_text(f"✅ {title} @ {company} — candidature validée !")

    elif action == "regen":
        sb.table("applications").delete().eq("user_job_id", item_id).eq("status", "draft").execute()
        await query.edit_message_text(f"🔄 {title} @ {company} — régénération en cours...")
        asyncio.create_task(
            _run_candidature_pipeline(user_id, item_id, query.message.chat_id, context.bot)
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _get_monthly_cost(sb, user_id: str) -> float:
    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
    result = (
        sb.table("llm_usage")
        .select("cost_usd")
        .eq("user_id", user_id)
        .gte("created_at", month_start)
        .execute()
    )
    return sum(row.get("cost_usd", 0) for row in (result.data or []))


# ---------------------------------------------------------------------------
# Bot lifecycle
# ---------------------------------------------------------------------------

def build_application() -> Application:
    settings = get_settings()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("companies", cmd_companies))
    app.add_handler(CommandHandler("costs", cmd_costs))
    app.add_handler(CommandHandler("preferences", cmd_preferences))
    app.add_handler(CommandHandler("prepare", cmd_prepare))
    app.add_handler(CallbackQueryHandler(handle_callback))
    return app


async def start_bot():
    """Start the Telegram bot in long-polling mode. Runs as an asyncio task."""
    global _app
    logger.info("Starting Telegram bot...")
    _app = build_application()
    await _app.initialize()
    await _app.start()
    await _app.updater.start_polling(drop_pending_updates=True)
    logger.info("Telegram bot started")
    # Keep running until cancelled
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Telegram bot stopping...")
        await _app.updater.stop()
        await _app.stop()
        await _app.shutdown()


def get_bot() -> Bot | None:
    """Get the bot instance for sending messages from other modules."""
    if _app:
        return _app.bot
    return None
