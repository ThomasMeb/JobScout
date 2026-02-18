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
Évalue l'offre selon ces 5 critères. Sois précis, utilise toute l'échelle (pas uniquement des multiples de 5).

1. skills (0-30) : Match entre les compétences techniques demandées et le profil (langages, frameworks, outils)
2. seniority (0-25) : Adéquation du niveau d'expérience demandé vs le profil candidat
3. location (0-20) : Compatibilité lieu de travail / remote policy avec les préférences
4. domain (0-15) : Qualité de la mission et orientation produit. Le candidat est orienté produit et secteur-agnostique : le secteur d'activité (fintech, retail, santé, industrie…) n'a AUCUNE importance. Évalue uniquement : la mission est-elle intéressante ? Y a-t-il un vrai impact produit/business ? Le rôle est-il orienté construction/amélioration de produit plutôt que maintenance pure ?
5. compensation (0-10) : Cohérence de la rémunération avec les attentes (si non précisé, mettre 5)

IMPORTANT : Le candidat a travaillé dans l'insurtech et l'e-commerce par opportunité, PAS par préférence sectorielle. Ne pas favoriser ces secteurs. Tous les secteurs se valent tant que la mission et le rôle produit sont intéressants.
{feedback_instructions}
Réponds STRICTEMENT au format JSON suivant (pas de markdown, pas de commentaires) :
{{
  "skills": <0-30>,
  "seniority": <0-25>,
  "location": <0-20>,
  "domain": <0-15>,
  "compensation": <0-10>,
  "match_keywords": ["keyword1", "keyword2"],
  "missing_keywords": ["keyword1"],
  "reasoning": "<explication en 1-2 phrases>",
  "language": "<fr|en>"
}}"""


async def score_new_jobs(conn: sqlite3.Connection) -> int:
    """Score all unscored jobs. Returns count of scored jobs."""
    cfg = load_config()
    profile = load_profile_text()

    # Inject feedback preferences if enough data
    feedback_text = generate_preference_summary(conn)
    if feedback_text:
        feedback_section = f"\nPREFERENCES UTILISATEUR (basées sur le feedback) :\n{feedback_text}\n"
        feedback_instructions = ("- Tiens compte des préférences utilisateur dans les sous-scores skills et domain\n"
                                 "- Keywords préférés → bonus sur skills/domain, keywords évités → malus sur skills/domain")
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
    """Parse the LLM JSON response with structured sub-scores."""
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

    # Extract sub-scores with bounds clamping
    sub = {
        "skills": min(max(float(result.get("skills", 0)), 0), 30),
        "seniority": min(max(float(result.get("seniority", 0)), 0), 25),
        "location": min(max(float(result.get("location", 0)), 0), 20),
        "domain": min(max(float(result.get("domain", 0)), 0), 15),
        "compensation": min(max(float(result.get("compensation", 0)), 0), 10),
    }
    score = sum(sub.values())

    # Derive priority from total score
    if score >= 75:
        priority = "high"
    elif score >= 50:
        priority = "medium"
    else:
        priority = "low"

    # Format reasoning with sub-score breakdown
    raw_reasoning = result.get("reasoning", "")
    breakdown = (f"Skills: {sub['skills']:.0f}/30 | Séniorité: {sub['seniority']:.0f}/25 | "
                 f"Loc: {sub['location']:.0f}/20 | Domaine: {sub['domain']:.0f}/15 | "
                 f"Rém: {sub['compensation']:.0f}/10")
    reasoning = f"{breakdown}\n{raw_reasoning}" if raw_reasoning else breakdown

    return {
        "score": score,
        "match_keywords": result.get("match_keywords", []),
        "missing_keywords": result.get("missing_keywords", []),
        "reasoning": reasoning,
        "language": result.get("language", "fr"),
        "priority": priority,
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
