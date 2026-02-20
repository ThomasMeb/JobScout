"""Pipeline de candidature — CV PDF, lettre de motivation, tips LinkedIn."""

import json
import logging
import re
import sqlite3
import subprocess
import tempfile
from pathlib import Path

from job_agent.config import (
    APPLICATIONS_DIR,
    TEMPLATES_DIR,
    load_config,
    load_cv,
    load_profile_text,
)
from job_agent.llm import call_llm, estimate_cost
from job_agent.storage import log_llm_usage

logger = logging.getLogger(__name__)

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
- Le projet "Alla2" doit etre nomme "Grada" (prediction BTC, vault DeFi sur Polygon)
- Tu peux reformuler les bullets et omettre des experiences peu pertinentes, mais JAMAIS changer l'ordre chronologique des experiences conservees

REGLE N°4 — LANGUE :
- Redige le CV en {language}
- Utilise les accents corrects (experience, competences, etc.)

Reponds en JSON strict (pas de markdown, pas de commentaires) :
{{
  "full_name": "...",
  "contact_line": "ville | tel | email",
  "links_line": "linkedin.com/in/thomasmebarki | github.com/ThomasMeb",
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
    job: dict,
    conn: sqlite3.Connection,
    language: str = "auto",
) -> dict:
    """Orchestrate the full application pipeline for a job.

    Returns dict with paths and cost: {cv_pdf, cover_letter, linkedin_tips, total_cost}
    """
    cfg = load_config()
    model = cfg["llm"]["model"]

    if language == "auto":
        language = _detect_language(job)

    company_name = job.get("company", "unknown")
    job_dir = APPLICATIONS_DIR / _safe_name(company_name) / _safe_name(job["title"])
    job_dir.mkdir(parents=True, exist_ok=True)

    total_cost = 0.0
    result = {"cv_pdf": None, "cover_letter": None, "linkedin_tips": None, "total_cost": 0.0}

    # Step 1 — Tailor CV via LLM
    logger.info(f"[Candidature] Step 1/4 — Tailoring CV for {job['title']} @ {company_name}")
    cv_master = load_cv(language)
    description = (job.get("description") or "")[:4000]

    lang_label = "francais" if language == "fr" else "anglais"

    tailoring_response, in_tok, out_tok = await call_llm(
        "Tu es un expert en recrutement tech et optimisation ATS. "
        "Tu adaptes des CV pour maximiser le taux de match avec les offres d'emploi. "
        "Tu reponds UNIQUEMENT en JSON valide, sans markdown ni commentaire.",
        TAILORING_PROMPT.format(
            cv_master=cv_master,
            job_title=job["title"],
            company=company_name,
            location=job.get("location") or "Non precise",
            description=description,
            language=lang_label,
        ),
        max_tokens=cfg["llm"]["max_tokens_tailoring"],
        temperature=cfg["llm"]["temperature_tailoring"],
    )
    cost = estimate_cost(model, in_tok, out_tok)
    total_cost += cost
    log_llm_usage(conn, "tailoring", job["id"], model, in_tok, out_tok, cost)

    cv_data = _parse_json_response(tailoring_response)
    if not cv_data:
        logger.error("[Candidature] Failed to parse tailoring response")
        return result

    # Enforce reverse chronological order (failsafe if LLM ignores the instruction)
    if cv_data.get("experiences"):
        cv_data["experiences"] = _sort_experiences_reverse_chrono(cv_data["experiences"])

    # Step 2 — Generate PDF
    logger.info("[Candidature] Step 2/4 — Generating PDF")
    labels = _get_labels(language)
    cv_template = cfg.get("candidature", {}).get("cv_template", "classic")
    pdf_path = _generate_pdf(cv_data, labels, job_dir, template_name=cv_template)
    result["cv_pdf"] = pdf_path

    # Step 3 — Cover letter
    logger.info("[Candidature] Step 3/4 — Generating cover letter")
    profile_summary = load_profile_text()[:2000]
    cv_summary = cv_data.get("profile_text", "")

    cover_response, in_tok, out_tok = await call_llm(
        "Tu es un redacteur senior specialise en candidatures tech. "
        "Tu ecris des emails de candidature concis, percutants et authentiques. "
        "Tu evites le jargon corporatif et les formulations creuses.",
        COVER_LETTER_PROMPT.format(
            profile_summary=profile_summary,
            cv_summary=cv_summary,
            job_title=job["title"],
            company=company_name,
            location=job.get("location") or "Non precise",
            description=description[:2000],
            candidate_name=cv_data.get("full_name", "Thomas Mebarki"),
            language=lang_label,
        ),
        max_tokens=cfg["llm"]["max_tokens_cover_letter"],
        temperature=cfg["llm"]["temperature_tailoring"],
    )
    cost = estimate_cost(model, in_tok, out_tok)
    total_cost += cost
    log_llm_usage(conn, "cover_letter", job["id"], model, in_tok, out_tok, cost)

    cover_path = job_dir / "cover_letter.md"
    cover_path.write_text(cover_response, encoding="utf-8")
    result["cover_letter"] = cover_path

    # Step 4 — LinkedIn tips
    logger.info("[Candidature] Step 4/4 — Generating LinkedIn tips")
    tips_response, in_tok, out_tok = await call_llm(
        "Tu es un expert en networking LinkedIn et strategie de candidature dans le secteur tech/ML. "
        "Tu donnes des conseils specifiques et actionnables, jamais generiques.",
        LINKEDIN_TIPS_PROMPT.format(
            job_title=job["title"],
            company=company_name,
            location=job.get("location") or "Non precise",
            description_excerpt=description[:800],
            candidate_name=cv_data.get("full_name", "Thomas Mebarki"),
            candidate_profile=cv_data.get("profile_text", "ML Engineer"),
            language=lang_label,
        ),
        max_tokens=1024,
        temperature=0.5,
    )
    cost = estimate_cost(model, in_tok, out_tok)
    total_cost += cost
    log_llm_usage(conn, "linkedin_tips", job["id"], model, in_tok, out_tok, cost)

    tips_path = job_dir / "linkedin_tips.md"
    tips_path.write_text(tips_response, encoding="utf-8")
    result["linkedin_tips"] = tips_path

    result["total_cost"] = round(total_cost, 6)

    # Record in applications table
    _save_application(conn, job["id"], result, language)

    logger.info(f"[Candidature] Done — cost: ${total_cost:.4f} — files in {job_dir}")
    return result


def _detect_language(job: dict) -> str:
    """Heuristic to detect job language (fr/en)."""
    text = f"{job.get('title', '')} {job.get('description', '')[:500]}".lower()
    fr_markers = ["poste", "nous recherchons", "profil", "missions", "competences",
                  "experience", "equipe", "entreprise", "candidature", "contrat"]
    en_markers = ["we are looking", "you will", "requirements", "responsibilities",
                  "team", "experience with", "must have", "nice to have", "apply"]
    fr_score = sum(1 for m in fr_markers if m in text)
    en_score = sum(1 for m in en_markers if m in text)
    return "fr" if fr_score >= en_score else "en"


def _latex_escape(text: str) -> str:
    """Escape special LaTeX characters."""
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
    """Sort experiences by start date, most recent first.

    Parses dates like 'Aout 2025 - Present', 'Jan 2023 - Nov 2023', etc.
    """
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
        # Extract start portion (before " - " or " – ")
        start = re.split(r'\s*[-–]\s*', dates_str)[0].strip().lower()
        # Remove accents for matching
        start = start.replace("é", "e").replace("û", "u")
        # Find year
        year_match = re.search(r'(\d{4})', start)
        year = int(year_match.group(1)) if year_match else 0
        # Find month
        month = 1
        for key, val in month_map.items():
            if key in start:
                month = val
                break
        # "present" / "présent" → far future
        if "present" in dates_str.lower().replace("é", "e"):
            return (9999, 12)
        return (year, month)

    try:
        return sorted(experiences, key=_parse_start_date, reverse=True)
    except Exception:
        return experiences


def _safe_name(name: str) -> str:
    """Convert a name to a safe directory name."""
    safe = re.sub(r'[^\w\s-]', '', name.strip())
    safe = re.sub(r'[\s]+', '_', safe)
    return safe[:80].lower()


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
            "key_skills": "Key skills",
        }
    return {
        "profile": "Profil",
        "skills": "Comp\\'etences Techniques",
        "experience": "Exp\\'erience Professionnelle",
        "education": "Formation",
        "certifications": "Certifications",
        "projects": "Projets",
        "languages": "Langues",
        "key_skills": "Comp\\'etences cl\\'es",
    }


def _generate_pdf(cv_data: dict, labels: dict, output_dir: Path, template_name: str = "classic") -> Path | None:
    """Fill the LaTeX template with cv_data and compile to PDF."""
    template_path = TEMPLATES_DIR / f"cv_{template_name}.tex"
    if not template_path.exists():
        # Fallback chain: requested → classic → legacy cv_template.tex
        template_path = TEMPLATES_DIR / "cv_classic.tex"
        if not template_path.exists():
            template_path = TEMPLATES_DIR / "cv_template.tex"
    if not template_path.exists():
        logger.error(f"LaTeX template not found: {template_path}")
        return None

    template = template_path.read_text(encoding="utf-8")

    # Build sections
    skills_block = _build_skills_block(cv_data.get("skills", []))
    experience_block = _build_experience_block(cv_data.get("experiences", []), labels)
    education_block = _build_education_block(cv_data.get("education", []))
    certifications_section = _build_certifications_section(cv_data.get("certifications", []), labels)
    projects_section = _build_projects_section(cv_data.get("projects", []), labels)
    languages_block = _build_languages_block(cv_data.get("languages", []))

    # Replace placeholders
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

    # Compile in temp dir then copy PDF
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = Path(tmpdir) / "cv.tex"
        tex_file.write_text(tex_content, encoding="utf-8")

        try:
            for _ in range(2):  # Run twice for references
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, str(tex_file)],
                    capture_output=True, timeout=30,
                )
            pdf_source = Path(tmpdir) / "cv.pdf"
            if pdf_source.exists():
                pdf_dest = output_dir / "cv.pdf"
                pdf_dest.write_bytes(pdf_source.read_bytes())
                logger.info(f"PDF generated: {pdf_dest}")
                return pdf_dest
            else:
                log_file = Path(tmpdir) / "cv.log"
                if log_file.exists():
                    log_content = log_file.read_text(encoding="utf-8", errors="replace")
                    # Find errors in log
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


def _build_experience_block(experiences: list, labels: dict) -> str:
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
    """Parse LLM JSON response, handling markdown wrapping."""
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON response: {text[:200]}")
        return None


def _save_application(conn: sqlite3.Connection, job_id: int, result: dict, language: str):
    """Save application record to DB."""
    conn.execute(
        """INSERT INTO applications (job_id, cv_path, cover_letter_path, linkedin_tips_path,
           language, cost_usd, status) VALUES (?, ?, ?, ?, ?, ?, 'draft')""",
        (
            job_id,
            str(result["cv_pdf"]) if result["cv_pdf"] else None,
            str(result["cover_letter"]) if result["cover_letter"] else None,
            str(result["linkedin_tips"]) if result["linkedin_tips"] else None,
            language,
            result["total_cost"],
        ),
    )
    conn.commit()
