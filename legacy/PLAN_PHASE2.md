# Job Agent — Phase 2 : Plan d'implémentation

## Vue d'ensemble

3 grands axes :
1. **Recherche proactive d'entreprises** (La Bonne Boite + liste cibles)
2. **Candidatures spontanées semi-auto** (préparation dossier → notification → /resume-tailoring)
3. **Sync Notion** (base de données centralisée pour le suivi)

---

## Axe 1 : Recherche d'entreprises cibles

### 1.1 — Nouveau module `job_agent/company_research.py`

**Source A : La Bonne Boite (API France Travail — accès libre)**
- Endpoint : `https://api.francetravail.io/partenaire/labonneboite/v1/company/`
- Recherche par code ROME + localisation → entreprises à fort potentiel d'embauche
- Codes ROME pertinents : M1805 (Data/BI), M1810 (Production informatique)
- Réutilise le token France Travail déjà configuré

**Source B : Liste manuelle d'entreprises cibles**
- Nouveau fichier `config.yaml` → section `target_companies`
- Liste de domaines/noms d'entreprises à surveiller (startups IA, scale-ups ML)
- Scraping de leurs pages carrières pour détecter des ouvertures

### 1.2 — Nouveau scraper `job_agent/scrapers/career_pages.py`

- Pour chaque entreprise cible : vérifier la page carrières
- Extraire les offres ouvertes (parsing HTML basique)
- Si aucune offre ML trouvée → candidature spontanée possible
- Stocker dans une nouvelle table `companies`

### 1.3 — Schéma DB : table `companies`

```sql
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    website TEXT,
    careers_url TEXT,
    sector TEXT,
    location TEXT,
    source TEXT,  -- 'labonneboite' | 'manual' | 'discovered'
    relevance_score REAL,
    has_open_ml_roles BOOLEAN DEFAULT FALSE,
    last_checked_at TIMESTAMP,
    spontaneous_status TEXT DEFAULT 'pending',
    -- pending | prepared | sent | responded | rejected
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Axe 2 : Candidatures spontanées semi-auto

### 2.1 — Workflow

```
Entreprise cible détectée (score élevé, pas d'offre ML ouverte)
    │
    ▼
Agent prépare un dossier :
    ├─ Fiche entreprise (activité, taille, stack tech, culture)
    ├─ Points de match avec le profil Thomas
    ├─ Suggestion d'angle d'approche
    └─ Contact RH si trouvable
    │
    ▼
Notification Telegram :
    "🏢 Entreprise cible : {name}
     Pas d'offre ML ouverte, mais potentiel élevé.
     [📄 Préparer candidature] [❌ Ignorer]"
    │
    ▼ (clic sur "Préparer candidature")
    │
Agent génère un fichier de brief :
    data/applications/spontaneous/{company_name}/brief.md
    Contient : contexte entreprise + angle + prompt prêt pour /resume-tailoring
    │
    ▼
Notification Telegram :
    "Brief prêt. Lance dans Claude Code :
     /resume-tailoring {path_to_brief}"
    │
    ▼ (utilisateur lance le skill manuellement)
    │
CV taillé + lettre générés par le skill resume-tailoring
    │
    ▼
Mise à jour Notion : status = "prepared"
```

### 2.2 — Module `job_agent/application_prep.py`

- `prepare_company_brief(company)` → génère le brief MD
- `prepare_job_brief(job)` → même chose pour les offres score >= 90
- Utilise DeepSeek pour synthétiser les infos entreprise
- Stocke dans `data/applications/`

### 2.3 — Nouvelles commandes Telegram

- `/companies` → liste les entreprises cibles avec statut
- `/prepare {id}` → déclenche la préparation du dossier
- Bouton "Préparer candidature" dans les notifications

---

## Axe 3 : Sync Notion

### 3.1 — Setup

- Dépendance : `notion-sdk` (pip)
- Variables d'environnement : `NOTION_TOKEN` + `NOTION_DATABASE_ID`
- Nouveau module : `job_agent/notion_sync.py`

### 3.2 — Schéma Notion (base de données)

| Propriété | Type | Mapping SQLite |
|-----------|------|----------------|
| Titre | title | jobs.title |
| Entreprise | text | jobs.company |
| Score | number | jobs.match_score |
| Priorité | select | jobs.match_priority |
| Statut | select | jobs.status |
| Localisation | text | jobs.location |
| Remote | select | jobs.remote_type |
| Salaire | text | salary_min-salary_max |
| Source | select | jobs.source |
| Lien offre | url | jobs.source_url |
| Keywords match | text | jobs.match_keywords |
| Reasoning | text | jobs.match_reasoning |
| Date scrape | date | jobs.scraped_at |
| Type | select | "offre" / "spontanée" |
| CV path | text | applications.cv_path |
| Notes | text | jobs.user_notes |

### 3.3 — Sync bidirectionnelle

- **SQLite → Notion** : après chaque cycle de scoring, push les jobs score >= 60
- **Notion → SQLite** : quand le statut change dans Notion (webhook ou polling)
- Ajout d'un champ `notion_page_id` dans la table `jobs` pour le mapping

### 3.4 — Intégration dans le pipeline

```
run_cycle() existant :
    1. Scrape → 2. Score → 3. Notify Telegram
                                    │
    NOUVEAU :                       │
    4. Company research ────────────┤
    5. Sync Notion ─────────────────┘
```

---

## Fichiers à créer/modifier

### Nouveaux fichiers
- `job_agent/company_research.py` — recherche d'entreprises
- `job_agent/scrapers/career_pages.py` — scraping pages carrières
- `job_agent/application_prep.py` — préparation dossiers candidature
- `job_agent/notion_sync.py` — synchronisation Notion

### Fichiers à modifier
- `config.yaml` — sections `target_companies`, `notion`, codes ROME
- `.env` / `.env.example` — `NOTION_TOKEN`, `NOTION_DATABASE_ID`
- `storage.py` — table `companies`, champ `notion_page_id` sur `jobs`
- `scheduler.py` — intégrer company research + notion sync dans `run_cycle()`
- `notifier.py` — commandes `/companies`, `/prepare`, boutons spontanée
- `requirements.txt` — `notion-sdk`

---

## Ordre d'implémentation

1. **Notion sync** (plus simple, valeur immédiate) ~1h
2. **Table companies + La Bonne Boite** ~1h
3. **Liste cibles manuelle + career pages scraper** ~1h
4. **Application prep + brief generator** ~1h
5. **Intégration Telegram (commandes + boutons)** ~30min
6. **Tests end-to-end** ~30min

Total estimé : ~5h de dev
