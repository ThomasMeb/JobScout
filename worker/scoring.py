"""Scoring module for multi-tenant worker.

Contains the LLM client, scoring prompt, and response parser.
Adapted from job_agent/matcher.py and job_agent/llm.py to work
with Supabase profiles instead of config.yaml.
"""
import json
import logging

from openai import AsyncOpenAI

from worker.config import get_settings

logger = logging.getLogger(__name__)

# DeepSeek pricing (per million tokens)
PRICING = {
    "deepseek-chat": {"input": 0.28, "output": 1.10, "cache_hit": 0.028},
}

SCORING_SYSTEM_PROMPT = """Tu es un expert en recrutement ML/Data Science. Tu évalues la compatibilité entre un profil candidat et une offre d'emploi.

PROFIL CANDIDAT :
{profile}

INSTRUCTIONS :
Évalue l'offre selon ces 5 critères. Sois précis, utilise toute l'échelle (pas uniquement des multiples de 5).

1. skills (0-30) : Match entre les compétences techniques demandées et le profil (langages, frameworks, outils)
2. seniority (0-25) : Adéquation du niveau d'expérience demandé vs le profil candidat
3. location (0-20) : Compatibilité lieu de travail / remote policy avec les préférences
4. domain (0-15) : Qualité de la mission et orientation produit. Le candidat est orienté produit et secteur-agnostique : le secteur d'activité (fintech, retail, santé, industrie…) n'a AUCUNE importance. Évalue uniquement : la mission est-elle intéressante ? Y a-t-il un vrai impact produit/business ? Le rôle est-il orienté construction/amélioration de produit plutôt que maintenance pure ?
5. compensation (0-10) : Cohérence de la rémunération avec les attentes (si non précisé, mettre 5)

IMPORTANT : Le candidat a travaillé dans l'insurtech et l'e-commerce par opportunité, PAS par préférence sectorielle. Ne pas favoriser ces secteurs. Tous les secteurs se valent tant que la mission et le rôle produit sont intéressants.

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


def _get_llm_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.2,
) -> tuple[str, int, int]:
    """Call DeepSeek and return (response_text, input_tokens, output_tokens)."""
    settings = get_settings()
    client = _get_llm_client()

    response = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    text = response.choices[0].message.content or ""
    input_tokens = response.usage.prompt_tokens if response.usage else 0
    output_tokens = response.usage.completion_tokens if response.usage else 0
    return text, input_tokens, output_tokens


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = PRICING.get(model, PRICING["deepseek-chat"])
    cost = (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
    return round(cost, 6)


def parse_scoring_response(response: str) -> dict:
    """Parse the LLM JSON response with structured sub-scores."""
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse scoring JSON: {text[:200]}")
        return {
            "score": 0,
            "match_keywords": [],
            "missing_keywords": [],
            "reasoning": "Parsing error",
            "priority": "low",
        }

    sub = {
        "skills": min(max(float(result.get("skills", 0)), 0), 30),
        "seniority": min(max(float(result.get("seniority", 0)), 0), 25),
        "location": min(max(float(result.get("location", 0)), 0), 20),
        "domain": min(max(float(result.get("domain", 0)), 0), 15),
        "compensation": min(max(float(result.get("compensation", 0)), 0), 10),
    }
    score = sum(sub.values())

    if score >= 75:
        priority = "high"
    elif score >= 50:
        priority = "medium"
    else:
        priority = "low"

    raw_reasoning = result.get("reasoning", "")
    breakdown = (
        f"Skills: {sub['skills']:.0f}/30 | Séniorité: {sub['seniority']:.0f}/25 | "
        f"Loc: {sub['location']:.0f}/20 | Domaine: {sub['domain']:.0f}/15 | "
        f"Rém: {sub['compensation']:.0f}/10"
    )
    reasoning = f"{breakdown}\n{raw_reasoning}" if raw_reasoning else breakdown

    return {
        "score": score,
        "match_keywords": result.get("match_keywords", []),
        "missing_keywords": result.get("missing_keywords", []),
        "reasoning": reasoning,
        "priority": priority,
    }


def format_salary(salary_min: int | None, salary_max: int | None, currency: str = "EUR") -> str:
    if salary_min and salary_max:
        return f"{salary_min}-{salary_max} {currency}"
    if salary_min:
        return f"{salary_min}+ {currency}"
    if salary_max:
        return f"up to {salary_max} {currency}"
    return "Non précisé"
