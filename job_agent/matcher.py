import json
import logging
import sqlite3

from job_agent.config import load_config, load_profile_text
from job_agent.feedback_loop import generate_preference_summary
from job_agent.llm import call_llm, estimate_cost
from job_agent.storage import get_unscored_jobs, update_job_score, log_llm_usage

logger = logging.getLogger(__name__)

SCORING_SYSTEM_PROMPT = """Tu es un expert en recrutement ML/Data Science. Tu évalues la compatibilité entre un profil candidat et une offre d'emploi.

PROFIL CANDIDAT :
{profile}
{feedback_section}
INSTRUCTIONS :
- Évalue la compatibilité globale sur 100
- Identifie les mots-clés qui matchent et ceux qui manquent
- Donne une priorité (high/medium/low)
- Sois réaliste : un score > 80 signifie très bon match
{feedback_instructions}
Réponds STRICTEMENT au format JSON suivant (pas de markdown, pas de commentaires) :
{{
  "score": <0-100>,
  "match_keywords": ["keyword1", "keyword2"],
  "missing_keywords": ["keyword1"],
  "reasoning": "<explication en 2-3 phrases>",
  "language": "<fr|en>",
  "priority": "<high|medium|low>"
}}"""


async def score_new_jobs(conn: sqlite3.Connection) -> int:
    """Score all unscored jobs. Returns count of scored jobs."""
    cfg = load_config()
    profile = load_profile_text()

    # Inject feedback preferences if enough data
    feedback_text = generate_preference_summary(conn)
    if feedback_text:
        feedback_section = f"\nPREFERENCES UTILISATEUR (basées sur le feedback) :\n{feedback_text}\n"
        feedback_instructions = ("- Applique un bonus de +5 points si l'offre contient des keywords préférés par le candidat\n"
                                 "- Applique un malus de -5 points si l'offre contient des keywords évités par le candidat")
    else:
        feedback_section = ""
        feedback_instructions = ""

    system_prompt = SCORING_SYSTEM_PROMPT.format(
        profile=profile,
        feedback_section=feedback_section,
        feedback_instructions=feedback_instructions,
    )
    model = cfg["llm"]["model"]
    max_tokens = cfg["llm"]["max_tokens_scoring"]
    temperature = cfg["llm"]["temperature_scoring"]

    unscored = get_unscored_jobs(conn)
    if not unscored:
        logger.info("No unscored jobs")
        return 0

    logger.info(f"Scoring {len(unscored)} jobs...")
    scored = 0

    for job in unscored:
        description = job["description"] or ""
        # Truncate long descriptions to control costs
        if len(description) > 3000:
            description = description[:3000] + "..."

        user_prompt = f"""OFFRE D'EMPLOI :
Titre : {job['title']}
Entreprise : {job['company']}
Localisation : {job['location'] or 'Non précisé'}
Tags : {job['tags'] or 'Aucun'}
Salaire : {_format_salary(job)}

Description :
{description}"""

        try:
            response, in_tokens, out_tokens = await call_llm(
                system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature
            )
            result = _parse_scoring_response(response)
            cost = estimate_cost(model, in_tokens, out_tokens)

            update_job_score(
                conn,
                job_id=job["id"],
                score=result["score"],
                reasoning=result["reasoning"],
                match_keywords=result["match_keywords"],
                missing_keywords=result["missing_keywords"],
                priority=result["priority"],
                tokens_in=in_tokens,
                tokens_out=out_tokens,
            )
            log_llm_usage(conn, "scoring", job["id"], model, in_tokens, out_tokens, cost)
            scored += 1
            logger.info(f"  [{scored}/{len(unscored)}] {job['title']} @ {job['company']} → {result['score']}/100")

        except Exception as e:
            logger.error(f"Failed to score job {job['id']} ({job['title']}): {e}")
            continue

    return scored


def _parse_scoring_response(response: str) -> dict:
    """Parse the LLM JSON response, handling markdown wrapping."""
    text = response.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse scoring JSON, using defaults. Raw: {text[:200]}")
        return {
            "score": 0,
            "match_keywords": [],
            "missing_keywords": [],
            "reasoning": "Parsing error",
            "language": "fr",
            "priority": "low",
        }

    return {
        "score": float(result.get("score", 0)),
        "match_keywords": result.get("match_keywords", []),
        "missing_keywords": result.get("missing_keywords", []),
        "reasoning": result.get("reasoning", ""),
        "language": result.get("language", "fr"),
        "priority": result.get("priority", "low"),
    }


def _format_salary(job: dict) -> str:
    s_min = job.get("salary_min")
    s_max = job.get("salary_max")
    currency = job.get("salary_currency", "EUR")
    if s_min and s_max:
        return f"{s_min}-{s_max} {currency}"
    if s_min:
        return f"{s_min}+ {currency}"
    if s_max:
        return f"up to {s_max} {currency}"
    return "Non précisé"
