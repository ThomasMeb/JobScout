# JobScout — Roadmap Prochaines Phases

> Statut actuel : 61 tests, 17 routes frontend, 5 scrapers actifs, Stripe billing, admin dashboard
> Dernière mise à jour : 25 fév 2026

---

## Phase 5 — Scrapers Playwright (HelloWork, APEC, FreeWork, WeLoveDevs)

### Contexte
4 scrapers sont 90% implémentés (parsing HTML/JSON) mais désactivés car les sites utilisent du rendu JS côté client. Il faut ajouter Playwright pour exécuter le JavaScript.

### Plan d'implémentation

**Étape 1 : Infrastructure Playwright**
- Ajouter `playwright>=1.40.0` à `worker/requirements.txt`
- Créer `job_agent/scrapers/browser.py` : singleton browser context partagé
  ```python
  async def get_browser_page() -> Page:
      # Lance le browser au premier appel, réutilise ensuite
      # Headless Chromium, bloque images/fonts pour perf
      # Timeout 30s par page
  ```
- Mettre à jour `worker/Dockerfile` : installer les dépendances Chromium
  ```dockerfile
  RUN playwright install chromium --with-deps
  ```

**Étape 2 : Adapter les 4 scrapers**
Chaque scraper garde sa logique de parsing existante. On remplace juste le fetch `httpx` par Playwright :

| Scraper | Stratégie | Particularités |
|---------|-----------|----------------|
| **HelloWork** | `page.goto()` + wait for `.card-list` | Pagination multi-page, delay 5s |
| **APEC** | API JSON primaire, Playwright fallback | Endpoint API `api-offres.apec.fr` parfois bloqué |
| **FreeWork** | Extraction `__NEXT_DATA__` via Playwright | SPA Next.js, JSON dans page source |
| **WeLoveDevs** | `__NUXT_DATA__` ou `__NEXT_DATA__` | Détection auto du framework |

**Étape 3 : Activer dans la config**
```python
# worker/config.py — SCRAPER_CONFIGS
"hellowork": {"enabled": True, "use_playwright": True},
"apec": {"enabled": True, "use_playwright": False},  # API d'abord
"freework": {"enabled": True, "use_playwright": True},
"welovedevs": {"enabled": True, "use_playwright": True},
```

**Étape 4 : Tests**
- Test unitaire : parsing HTML/JSON de chaque scraper (mock de la page)
- Test intégration : scrape réel d'une page (marqué `@pytest.mark.integration`)

### Fichiers modifiés
| Fichier | Action | ~Lignes |
|---------|--------|---------|
| `job_agent/scrapers/browser.py` | Créer | ~50 |
| `job_agent/scrapers/hellowork.py` | Modifier | ~15 |
| `job_agent/scrapers/apec.py` | Modifier | ~15 |
| `job_agent/scrapers/freework.py` | Modifier | ~15 |
| `job_agent/scrapers/welovedevs.py` | Modifier | ~15 |
| `worker/config.py` | Modifier | ~4 |
| `worker/requirements.txt` | Modifier | +1 |
| `worker/Dockerfile` | Modifier | +2 |
| `tests/test_scrapers.py` | Créer | ~80 |

### Risques
- Taille image Docker +300MB (Chromium)
- RAM worker Render : Playwright nécessite ~256MB RAM (starter = 512MB, OK)
- Rate limiting des sites : respecter delay 3-5s entre requêtes
- CAPTCHA/Cloudflare : HelloWork et APEC peuvent bloquer — prévoir fallback gracieux

---

## Phase 6 — Notion Sync Bidirectionnel

### Contexte
`worker/notion_sync.py` (348 lignes) fait le push DB → Notion. Il manque le pull Notion → DB pour que les changements de statut faits dans Notion se propagent.

### Plan d'implémentation

**Étape 1 : Pull des statuts depuis Notion**
```python
# worker/notion_sync.py — nouvelle fonction
async def pull_notion_changes(user_id: str) -> int:
    """Read Notion pages modified since last sync, update local DB."""
    # 1. Query Notion DB with filter: last_edited_time > last_sync_at
    # 2. For each page, check if notion_page_id exists in user_jobs
    # 3. Compare Statut: si différent, update local status
    # 4. Sync user_notes from Notion "Notes" property
    # Return count of updated jobs
```

**Étape 2 : Ajouter les colonnes manquantes**
- Migration : `ALTER TABLE profiles ADD COLUMN notion_last_sync_at TIMESTAMPTZ`
- Notion property : ajouter "Notes" (rich text) aux jobs database

**Étape 3 : Intégrer dans le cycle worker**
```python
# worker/main.py — dans run_cycle()
# Après sync_all_users() (push)
from worker.notion_sync import pull_all_users
await pull_all_users()  # bidirectional
```

**Étape 4 : Gestion des conflits**
- Règle simple : **Notion gagne** pour le statut (l'user modifie dans Notion)
- **DB gagne** pour les données techniques (score, keywords, reasoning)
- Timestamp `notion_last_sync_at` pour éviter les boucles

### Fichiers modifiés
| Fichier | Action | ~Lignes |
|---------|--------|---------|
| `worker/notion_sync.py` | Modifier | +80 (pull + conflict) |
| `supabase/migrations/010_notion_sync.sql` | Créer | ~5 |
| `worker/main.py` | Modifier | +3 |
| `tests/test_notion_sync.py` | Créer | ~40 |

---

## Phase 7 — Tests (objectif : 100+ tests)

### Couverture actuelle
- `test_api.py` : 12 tests (endpoints profile, jobs, health, CSV)
- `test_models.py` : 10 tests (validation Pydantic)
- `test_scoring.py` : 18 tests (parsing LLM, coûts, salaires)
- `test_worker.py` : 21 tests (config, auto_apply, mailto, plan)
- **Total : 61 tests**

### Modules non testés (priorité haute → basse)

**Priorité 1 — Backend routes manquantes**
```
tests/test_admin.py     — 6 tests : list_users, scrapers, metrics, 403 non-admin
tests/test_billing.py   — 5 tests : checkout, portal, webhook events, status
tests/test_stats.py     — 3 tests : stats endpoint, charts endpoint
```

**Priorité 2 — Worker modules critiques**
```
tests/test_notifications.py — 6 tests : build_digest_html, build_telegram_message,
                                         email filtering logic, send flow (mocked)
tests/test_candidature.py   — 4 tests : prepare_candidature, CV generation,
                                         cover letter format
tests/test_feedback_loop.py — 3 tests : keyword analysis, feedback stats
```

**Priorité 3 — Scrapers (parsing)**
```
tests/test_scrapers.py — 10 tests : parsing HTML fixtures pour chaque scraper,
                                     dedup, retry logic, RawJob validation
```

**Priorité 4 — Intégration**
```
tests/test_tasks.py    — 4 tests : scrape_global flow, score_per_user flow (mocked DB)
```

### Total estimé : ~41 nouveaux tests → 102 total

### Stratégie de mock
- **Supabase** : `unittest.mock.MagicMock` pour `get_supabase()`
- **HTTP** : `httpx.MockTransport` ou `respx` pour API externes
- **Telegram** : Mock `Bot` et `Update` objects
- **Stripe** : Mock `stripe.Webhook.construct_event`

---

## Phase 8 — UX / Polish

### 8a. Dashboard Mobile

**Problème** : Le tableau de jobs est inutilisable sur mobile (scroll horizontal, 14+ colonnes).

**Solution** : Vue carte responsive

```tsx
// Breakpoint md: (768px)
// Desktop : tableau actuel
// Mobile : cartes empilées

<div className="hidden md:block">
  <JobTable ... />  {/* Tableau desktop */}
</div>
<div className="md:hidden space-y-3">
  {jobs.map(job => <JobCard key={job.id} job={job} />)}
</div>
```

**JobCard mobile** (~40 lignes) :
- Score badge coloré (vert/jaune/gris)
- Titre + Entreprise
- Location + Remote badge
- Boutons : Voir / Intéressé / Ignorer

**Navigation mobile** :
- Hamburger menu (3 lignes) au lieu de liens inline
- Drawer latéral avec : Dashboard, Billing, Admin, Settings

### 8b. Filtres responsive

```tsx
// Mobile : bouton "Filtres" → drawer/modal
// Desktop : barre horizontale (actuel)
<button className="md:hidden">Filtres ({activeCount})</button>
<div className="hidden md:flex flex-wrap gap-3">
  {/* filtres actuels */}
</div>
```

### 8c. Emails transactionnels (Brevo)

| Email | Trigger | Template |
|-------|---------|----------|
| Welcome | Après signup + onboarding | Bienvenue + tips setup |
| Weekly digest | Chaque lundi 9h | Top 5 jobs de la semaine |
| Application sent | Auto-apply envoyé | Confirmation + récap |
| Subscription | Upgrade/downgrade | Merci + détails plan |

**Implémentation** :
- `worker/emails.py` (~100 lignes) : templates HTML + envoi Brevo
- Trigger depuis `notifications.py` et `auto_apply.py`

### 8d. Onboarding amélioré

- Indicateur de temps estimé ("~3 min")
- Validation en temps réel (pas juste au submit)
- Suggestions de keywords basées sur le CV collé
- Skip optionnel des étapes non essentielles

### Fichiers modifiés
| Fichier | Action | ~Lignes |
|---------|--------|---------|
| `frontend/src/components/JobCard.tsx` | Créer | ~60 |
| `frontend/src/components/MobileNav.tsx` | Créer | ~40 |
| `frontend/src/components/FilterDrawer.tsx` | Créer | ~50 |
| `frontend/src/app/dashboard/page.tsx` | Modifier | ~30 |
| `frontend/src/components/JobTable.tsx` | Modifier | ~5 |
| `worker/emails.py` | Créer | ~100 |
| `worker/notifications.py` | Modifier | ~10 |

---

## Ordre d'exécution recommandé

```
Phase 7 (Tests)          — 2-3h  — Fondation qualité
    ↓
Phase 5 (Playwright)     — 4-5h  — Doubler la couverture scraping
    ↓
Phase 8 (UX)             — 3-4h  — Mobile + emails
    ↓
Phase 6 (Notion bidi)    — 2-3h  — Nice-to-have
```

**Justification** : Tests d'abord pour sécuriser la base avant d'ajouter de la complexité (Playwright). UX ensuite car c'est visible par les utilisateurs. Notion en dernier car c'est optionnel.
