"""Pipeline de candidature — CV PDF, lettre de motivation, tips LinkedIn.

Adapted from legacy/job_agent/candidature.py for multi-tenant SaaS (Supabase).
"""

import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path

from worker.config import get_settings
from worker.db import get_supabase
from worker.scoring import call_llm, estimate_cost

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"

TAILORING_PROMPT = """Tu es un expert en recrutement tech specialise en ML/Data Science avec 15 ans d'experience en optimisation ATS.

## ETAPE 1 — EXTRACTION DES MOTS-CLES DE L'OFFRE

Avant d'adapter le CV, identifie mentalement :
- Les competences techniques explicitement demandees (langages, frameworks, outils)
- Les competences transversales (leadership, communication, agile...)
- Les termes recurrents dans la description (utilises 2+ fois = prioritaires)
- Le niveau d'experience attendu et le ton de l'offre

## CONTEXTE

CV MASTER DU CANDIDAT :
{cv_master}

OFFRE D'EMPLOI :
Titre : {job_title}
Entreprise : {company}
Localisation : {location}
Description :
{description}

## REGLES STRICTES

REGLE N°1 — ORDRE CHRONOLOGIQUE DECROISSANT (ABSOLUE, NON NEGOCIABLE) :
Les experiences DOIVENT etre triees par date de debut, de la plus recente a la plus ancienne.
Exemple correct : 2025, 2024, 2024, 2023, 2023, 2023.
Exemple INCORRECT : 2025, 2023, 2024 (desordre = INTERDIT).
NE JAMAIS reordonner par pertinence. La pertinence se gere dans le profil et les skills, PAS dans l'ordre des experiences.

REGLE N°2 — OPTIMISATION ATS :
- Integre les mots-cles extraits a l'etape 1 dans le profile_text ET dans les bullets d'experience
- Utilise les termes EXACTS de l'offre (pas de synonymes approximatifs)
- Place les competences les plus critiques dans les premieres lignes du profil
- Dans la section skills, priorise les categories qui matchent l'offre

REGLE N°3 — INTEGRITE :
- NE JAMAIS inventer d'experience, de competence ou de certification
- NE JAMAIS mentir sur les dates ou les entreprises
- Tu peux reformuler les bullets et omettre des experiences peu pertinentes, mais JAMAIS changer l'ordre chronologique des experiences conservees

REGLE N°4 — LANGUE :
- Redige le CV en {language}
- Utilise les accents corrects (experience, competences, etc.)

Reponds en JSON strict (pas de markdown, pas de commentaires) :
{{
  "full_name": "...",
  "contact_line": "ville | tel | email",
  "links_line": "linkedin | github",
  "profile_text": "resume adapte en 3-4 lignes integrant les mots-cles de l'offre",
  "skills": [
    {{"category": "Machine Learning", "items": "Scikit-learn, XGBoost, ..."}},
    ...
  ],
  "experiences": [
    {{
      "title": "titre du poste",
      "company": "entreprise",
      "dates": "Aout 2025 - Present",
      "description": "description du poste en 1 ligne",
      "bullets": ["bullet 1 avec keyword de l'offre", "bullet 2", "bullet 3"]
    }},
    ...
  ],
  "education": [
    {{"degree": "Master Data Science", "school": "CentraleSupelec", "year": "2023"}},
    ...
  ],
  "certifications": ["cert1", "cert2"],
  "projects": [
    {{"name": "nom", "description": "description courte"}},
    ...
  ],
  "languages": [
    {{"language": "Francais", "level": "Langue maternelle"}},
    ...
  ]
}}"""

COVER_LETTER_PROMPT = """Tu es un redacteur senior specialise en candidatures tech. Tu ecris des emails de candidature percutants et authentiques.

## PROFIL CANDIDAT :
{profile_summary}

## CV ADAPTE (resume) :
{cv_summary}

## OFFRE :
Titre : {job_title}
Entreprise : {company}
Localisation : {location}
Description : {description}

## STRUCTURE OBLIGATOIRE (4 parties) :

**1. Accroche (2-3 phrases)** : Mentionne le poste et l'entreprise. Commence par un fait concret (resultat chiffre, projet pertinent) — PAS par "Je me permets de vous contacter" ou "Passionné par".

**2. Valeur ajoutée (1 paragraphe)** : Connecte 2-3 experiences SPECIFIQUES du candidat aux besoins de l'offre. Chaque experience citee doit inclure un resultat mesurable ou un livrable concret.

**3. Motivation entreprise (1 paragraphe)** : Explique pourquoi CETTE entreprise en particulier (produit, mission, techno, culture). Pas de flatterie generique ("leader dans son domaine", "entreprise innovante").

**4. Conclusion (2-3 phrases)** : Proposition d'echange concret (call de 15 min, entretien). Pas de formule servile.

## REGLES :
- Format email direct (pas de lettre formelle avec adresse en-tete)
- Objet : Candidature {job_title} - {candidate_name}
- 250-350 mots maximum
- Ton professionnel, direct, humain — evite le langage corporatif creux
- INTERDITS : "passionné par l'IA", "leader dans son domaine", "fort de mes X années", "vivement intéressé", "n'hésitez pas"
- Langue : {language} — utilise les accents corrects (é, è, ê, à, ù, etc.)

Reponds directement avec le texte de l'email (pas de JSON, pas de markdown)."""

LINKEDIN_TIPS_PROMPT = """Tu es un expert en networking LinkedIn specialise dans le recrutement tech/ML.

## OFFRE :
Titre : {job_title}
Entreprise : {company}
Localisation : {location}
Description (extrait) : {description_excerpt}

## CANDIDAT : {candidate_name}
Profil resume : {candidate_profile}

## INSTRUCTIONS :

Genere un plan d'approche LinkedIn SPECIFIQUE a cette offre et cette entreprise. En markdown :

### 1. Cibles prioritaires
- 3 types de profils a contacter chez {company} (titre exact LinkedIn, ex: "Head of Data @{company}")
- Pourquoi chaque profil est strategique

### 2. Requetes LinkedIn (copier-coller)
- 3 requetes de recherche pretes a coller dans la barre LinkedIn
- Format : "{company}" "Data" OR "ML" — adapte aux titres reels de l'entreprise

### 3. Message d'approche
- Un message de 60-80 mots qui :
  - Mentionne le poste specifique ({job_title})
  - Cite un element concret du profil du candidat pertinent pour l'offre
  - Pose une question ouverte (pas "est-ce que vous recrutez")
- PAS de message generique type "Je suis tres interesse par votre entreprise"

### 4. Timing et strategie
- Meilleur moment pour envoyer
- Action de suivi si pas de reponse (delai, message)

Langue : {language}"""


async def prepare_candidature(
    user_id: str,
    user_job_id: int,
) -> dict:
    """Orchestrate the full application pipeline for a job.

    Returns dict with keys: cv_pdf_bytes, cover_letter, linkedin_tips, total_cost, status
    """
    sb = get_supabase()
    settings = get_settings()
    model = settings.deepseek_model

    result = {
        "cv_pdf_bytes": None,
        "cover_letter": None,
        "linkedin_tips": None,
        "total_cost": 0.0,
        "status": "error",
    }

    # Fetch user profile
    profile = (
        sb.table("profiles")
        .select("cv_text, profile_summary, name, monthly_budget_usd")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not profile.data:
        logger.error(f"[Candidature] Profile not found for user {user_id[:8]}")
        return result

    user = profile.data
    cv_master = user.get("cv_text") or user.get("profile_summary") or ""
    if not cv_master:
        logger.error(f"[Candidature] No CV text for user {user_id[:8]}")
        return result

    # Fetch job data via user_jobs JOIN raw_jobs
    uj = (
        sb.table("user_jobs")
        .select("id, raw_job_id, raw_jobs(title, company, location, description, source_url, apply_url, remote_type, salary_min, salary_max, salary_currency, source)")
        .eq("id", user_job_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not uj.data:
        logger.error(f"[Candidature] user_job {user_job_id} not found for user {user_id[:8]}")
        return result

    raw_job = uj.data.get("raw_jobs", {})
    job_title = raw_job.get("title", "")
    company_name = raw_job.get("company", "Unknown")
    description = (raw_job.get("description") or "")[:4000]
    location = raw_job.get("location") or "Non precise"

    # Detect language
    language = _detect_language(job_title, description)
    lang_label = "francais" if language == "fr" else "anglais"

    # Check budget before starting
    monthly_cost = _get_user_monthly_cost(sb, user_id)
    budget = float(user.get("monthly_budget_usd") or 5.0)
    if monthly_cost >= budget:
        logger.warning(f"[Candidature] Budget exhausted for user {user_id[:8]}")
        return result

    total_cost = 0.0

    # Step 1 — Tailor CV via LLM
    logger.info(f"[Candidature] Step 1/4 — Tailoring CV for {job_title} @ {company_name}")

    tailoring_response, in_tok, out_tok = await call_llm(
        "Tu es un expert en recrutement tech et optimisation ATS. "
        "Tu adaptes des CV pour maximiser le taux de match avec les offres d'emploi. "
        "Tu reponds UNIQUEMENT en JSON valide, sans markdown ni commentaire.",
        TAILORING_PROMPT.format(
            cv_master=cv_master,
            job_title=job_title,
            company=company_name,
            location=location,
            description=description,
            language=lang_label,
        ),
        max_tokens=settings.tailoring_max_tokens,
        temperature=settings.tailoring_temperature,
    )
    cost = estimate_cost(model, in_tok, out_tok)
    total_cost += cost
    _log_llm_usage(sb, user_id, "tailoring", user_job_id, model, in_tok, out_tok, cost)

    cv_data = _parse_json_response(tailoring_response)
    if not cv_data:
        logger.error("[Candidature] Failed to parse tailoring response")
        return result

    # Enforce reverse chronological order
    if cv_data.get("experiences"):
        cv_data["experiences"] = _sort_experiences_reverse_chrono(cv_data["experiences"])

    # Step 2 — Generate PDF
    logger.info("[Candidature] Step 2/4 — Generating PDF")
    labels = _get_labels(language)
    pdf_bytes = _generate_pdf(cv_data, labels, template_name=settings.cv_template)

    # Step 3 — Cover letter
    logger.info("[Candidature] Step 3/4 — Generating cover letter")
    profile_summary = cv_master[:2000]
    cv_summary = cv_data.get("profile_text", "")

    cover_response, in_tok, out_tok = await call_llm(
        "Tu es un redacteur senior specialise en candidatures tech. "
        "Tu ecris des emails de candidature concis, percutants et authentiques. "
        "Tu evites le jargon corporatif et les formulations creuses.",
        COVER_LETTER_PROMPT.format(
            profile_summary=profile_summary,
            cv_summary=cv_summary,
            job_title=job_title,
            company=company_name,
            location=location,
            description=description[:2000],
            candidate_name=cv_data.get("full_name", user.get("name", "")),
            language=lang_label,
        ),
        max_tokens=settings.cover_letter_max_tokens,
        temperature=settings.tailoring_temperature,
    )
    cost = estimate_cost(model, in_tok, out_tok)
    total_cost += cost
    _log_llm_usage(sb, user_id, "cover_letter", user_job_id, model, in_tok, out_tok, cost)

    # Step 4 — LinkedIn tips
    logger.info("[Candidature] Step 4/4 — Generating LinkedIn tips")
    tips_response, in_tok, out_tok = await call_llm(
        "Tu es un expert en networking LinkedIn et strategie de candidature dans le secteur tech/ML. "
        "Tu donnes des conseils specifiques et actionnables, jamais generiques.",
        LINKEDIN_TIPS_PROMPT.format(
            job_title=job_title,
            company=company_name,
            location=location,
            description_excerpt=description[:800],
            candidate_name=cv_data.get("full_name", user.get("name", "")),
            candidate_profile=cv_data.get("profile_text", ""),
            language=lang_label,
        ),
        max_tokens=1024,
        temperature=0.5,
    )
    cost = estimate_cost(model, in_tok, out_tok)
    total_cost += cost
    _log_llm_usage(sb, user_id, "linkedin_tips", user_job_id, model, in_tok, out_tok, cost)

    # Store PDF in Supabase Storage
    cv_storage_path = None
    if pdf_bytes:
        storage_path = f"{user_id}/{user_job_id}/cv.pdf"
        try:
            sb.storage.from_("applications").upload(
                storage_path, pdf_bytes, {"content-type": "application/pdf"}
            )
            cv_storage_path = storage_path
        except Exception as e:
            logger.warning(f"[Candidature] Storage upload failed: {e}")

    # Save application record
    sb.table("applications").upsert({
        "user_id": user_id,
        "user_job_id": user_job_id,
        "cv_storage_path": cv_storage_path,
        "cover_letter": cover_response,
        "linkedin_tips": tips_response,
        "language": language,
        "status": "draft",
        "cost_usd": round(total_cost, 6),
    }, on_conflict="user_id,user_job_id").execute()

    result.update({
        "cv_pdf_bytes": pdf_bytes,
        "cover_letter": cover_response,
        "linkedin_tips": tips_response,
        "total_cost": round(total_cost, 6),
        "status": "draft",
    })

    logger.info(f"[Candidature] Done — cost: ${total_cost:.4f}")
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_language(title: str, description: str) -> str:
    text = f"{title} {description[:500]}".lower()
    fr_markers = ["poste", "nous recherchons", "profil", "missions", "competences",
                  "experience", "equipe", "entreprise", "candidature", "contrat"]
    en_markers = ["we are looking", "you will", "requirements", "responsibilities",
                  "team", "experience with", "must have", "nice to have", "apply"]
    fr_score = sum(1 for m in fr_markers if m in text)
    en_score = sum(1 for m in en_markers if m in text)
    return "fr" if fr_score >= en_score else "en"


def _latex_escape(text: str) -> str:
    if not text:
        return ""
    replacements = [
        ("\\", "\\textbackslash{}"),
        ("&", "\\&"),
        ("%", "\\%"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("{", "\\{"),
        ("}", "\\}"),
        ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _sort_experiences_reverse_chrono(experiences: list) -> list:
    month_map = {
        "jan": 1, "fev": 2, "feb": 2, "mar": 3, "avr": 4, "apr": 4,
        "mai": 5, "may": 5, "jun": 6, "jui": 7, "jul": 7, "aou": 8, "aug": 8,
        "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        "janvier": 1, "fevrier": 2, "february": 2, "mars": 3, "march": 3,
        "avril": 4, "april": 4, "juin": 6, "june": 6, "juillet": 7, "july": 7,
        "aout": 8, "august": 8, "septembre": 9, "september": 9,
        "octobre": 10, "october": 10, "novembre": 11, "november": 11,
        "decembre": 12, "december": 12,
    }

    def _parse_start_date(exp):
        dates_str = exp.get("dates", "")
        start = re.split(r'\s*[-–]\s*', dates_str)[0].strip().lower()
        start = start.replace("é", "e").replace("û", "u")
        year_match = re.search(r'(\d{4})', start)
        year = int(year_match.group(1)) if year_match else 0
        month = 1
        for key, val in month_map.items():
            if key in start:
                month = val
                break
        if "present" in dates_str.lower().replace("é", "e"):
            return (9999, 12)
        return (year, month)

    try:
        return sorted(experiences, key=_parse_start_date, reverse=True)
    except Exception:
        return experiences


def _get_labels(language: str) -> dict:
    if language == "en":
        return {
            "profile": "Profile",
            "skills": "Technical Skills",
            "experience": "Professional Experience",
            "education": "Education",
            "certifications": "Certifications",
            "projects": "Projects",
            "languages": "Languages",
        }
    return {
        "profile": "Profil",
        "skills": "Comp\\'etences Techniques",
        "experience": "Exp\\'erience Professionnelle",
        "education": "Formation",
        "certifications": "Certifications",
        "projects": "Projets",
        "languages": "Langues",
    }


def _generate_pdf(cv_data: dict, labels: dict, template_name: str = "classic") -> bytes | None:
    """Fill the LaTeX template and compile to PDF. Returns PDF bytes or None."""
    template_path = TEMPLATES_DIR / f"cv_{template_name}.tex"
    if not template_path.exists():
        template_path = TEMPLATES_DIR / "cv_classic.tex"
        if not template_path.exists():
            template_path = TEMPLATES_DIR / "cv_template.tex"
    if not template_path.exists():
        logger.error(f"LaTeX template not found: {template_path}")
        return None

    template = template_path.read_text(encoding="utf-8")

    skills_block = _build_skills_block(cv_data.get("skills", []))
    experience_block = _build_experience_block(cv_data.get("experiences", []))
    education_block = _build_education_block(cv_data.get("education", []))
    certifications_section = _build_certifications_section(cv_data.get("certifications", []), labels)
    projects_section = _build_projects_section(cv_data.get("projects", []), labels)
    languages_block = _build_languages_block(cv_data.get("languages", []))

    replacements = {
        "<<FULL_NAME>>": _latex_escape(cv_data.get("full_name", "")),
        "<<CONTACT_LINE>>": _latex_escape(cv_data.get("contact_line", "")),
        "<<LINKS_LINE>>": _latex_escape(cv_data.get("links_line", "")),
        "<<LABEL_PROFILE>>": labels["profile"],
        "<<PROFILE_TEXT>>": _latex_escape(cv_data.get("profile_text", "")),
        "<<LABEL_SKILLS>>": labels["skills"],
        "<<SKILLS_BLOCK>>": skills_block,
        "<<LABEL_EXPERIENCE>>": labels["experience"],
        "<<EXPERIENCE_BLOCK>>": experience_block,
        "<<LABEL_EDUCATION>>": labels["education"],
        "<<EDUCATION_BLOCK>>": education_block,
        "<<CERTIFICATIONS_SECTION>>": certifications_section,
        "<<PROJECTS_SECTION>>": projects_section,
        "<<LABEL_LANGUAGES>>": labels["languages"],
        "<<LANGUAGES_BLOCK>>": languages_block,
    }

    tex_content = template
    for placeholder, value in replacements.items():
        tex_content = tex_content.replace(placeholder, value)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = Path(tmpdir) / "cv.tex"
        tex_file.write_text(tex_content, encoding="utf-8")

        try:
            for _ in range(2):
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, str(tex_file)],
                    capture_output=True, timeout=30,
                )
            pdf_source = Path(tmpdir) / "cv.pdf"
            if pdf_source.exists():
                pdf_bytes = pdf_source.read_bytes()
                logger.info("PDF generated successfully")
                return pdf_bytes
            else:
                log_file = Path(tmpdir) / "cv.log"
                if log_file.exists():
                    log_content = log_file.read_text(encoding="utf-8", errors="replace")
                    errors = [line for line in log_content.split("\n") if line.startswith("!")]
                    logger.error(f"pdflatex errors: {errors[:5]}")
                return None
        except subprocess.TimeoutExpired:
            logger.error("pdflatex timed out")
            return None
        except FileNotFoundError:
            logger.error("pdflatex not found — install texlive-base")
            return None


def _build_skills_block(skills: list) -> str:
    if not skills:
        return ""
    lines = []
    for skill in skills:
        cat = _latex_escape(skill.get("category", ""))
        items = _latex_escape(skill.get("items", ""))
        lines.append(f"\\textbf{{{cat}:}} {items}")
    return "\\\\\n".join(lines)


def _build_experience_block(experiences: list) -> str:
    if not experiences:
        return ""
    blocks = []
    for exp in experiences:
        title = _latex_escape(exp.get("title", ""))
        company = _latex_escape(exp.get("company", ""))
        dates = _latex_escape(exp.get("dates", ""))
        desc = _latex_escape(exp.get("description", ""))

        block = f"\\textbf{{{title}}} --- {company} \\hfill {dates}\\\\\n"
        if desc:
            block += f"\\textit{{{desc}}}\n"

        bullets = exp.get("bullets", [])
        if bullets:
            block += "\\begin{itemize}[leftmargin=1.5em, itemsep=1pt, parsep=0pt]\n"
            for bullet in bullets:
                block += f"  \\item {_latex_escape(bullet)}\n"
            block += "\\end{itemize}\n"

        blocks.append(block)
    return "\n".join(blocks)


def _build_education_block(education: list) -> str:
    if not education:
        return ""
    lines = []
    for edu in education:
        degree = _latex_escape(edu.get("degree", ""))
        school = _latex_escape(edu.get("school", ""))
        year = _latex_escape(str(edu.get("year", "")))
        lines.append(f"\\textbf{{{degree}}} --- {school} \\hfill {year}")
    return "\\\\\n".join(lines)


def _build_certifications_section(certifications: list, labels: dict) -> str:
    if not certifications:
        return ""
    items = "\n".join(f"  \\item {_latex_escape(c)}" for c in certifications)
    return (
        f"\\section{{{labels['certifications']}}}\n"
        f"\\begin{{itemize}}[leftmargin=1.5em, itemsep=1pt, parsep=0pt]\n"
        f"{items}\n"
        "\\end{itemize}"
    )


def _build_projects_section(projects: list, labels: dict) -> str:
    if not projects:
        return ""
    items = []
    for p in projects:
        name = _latex_escape(p.get("name", ""))
        desc = _latex_escape(p.get("description", ""))
        items.append(f"  \\item \\textbf{{{name}:}} {desc}")
    return (
        f"\\section{{{labels['projects']}}}\n"
        f"\\begin{{itemize}}[leftmargin=1.5em, itemsep=1pt, parsep=0pt]\n"
        + "\n".join(items) + "\n"
        "\\end{itemize}"
    )


def _build_languages_block(languages: list) -> str:
    if not languages:
        return ""
    lines = []
    for lang in languages:
        name = _latex_escape(lang.get("language", ""))
        level = _latex_escape(lang.get("level", ""))
        lines.append(f"\\textbf{{{name}:}} {level}")
    return " --- ".join(lines)


def _parse_json_response(response: str) -> dict | None:
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON response: {text[:200]}")
        return None


def _log_llm_usage(
    sb, user_id: str, operation: str, user_job_id: int,
    model: str, tokens_in: int, tokens_out: int, cost: float,
):
    sb.table("llm_usage").insert({
        "user_id": user_id,
        "operation": operation,
        "user_job_id": user_job_id,
        "model": model,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": cost,
    }).execute()


def _get_user_monthly_cost(sb, user_id: str) -> float:
    from datetime import datetime, timezone
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
