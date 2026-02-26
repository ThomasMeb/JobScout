# JobScout — Roadmap

> **140+ tests** | 18 routes frontend | **9 scrapers actifs** | Stripe billing | Admin dashboard | Notion bidi | Mobile responsive | Brevo emails | Scraper monitoring
> Dernière mise à jour : 26 fév 2026

---

## Phases terminées

### Phase 1-4 — Fondations (terminé)
- P1 : Schéma Supabase, scrapers WTTJ/RemoteOK/Adzuna/FranceTravail/JobSpy, scoring DeepSeek
- P2 : Landing page, pricing, auth, settings, Telegram bot, auto-apply, Notion push
- P3 : Stripe billing, plan limits, search, bulk actions, export CSV
- P4 : Structured logging, rate limiting, admin dashboard, worker heartbeat

### Phase 5 — Scrapers Playwright (terminé)
- `job_agent/scrapers/browser.py` : singleton Playwright, headless Chromium, bloque images/fonts
- HelloWork, APEC (API-first + Playwright fallback), FreeWork (`__NEXT_DATA__`), WeLoveDevs (`__NEXT_DATA__`/`__NUXT_DATA__`)
- 4 scrapers activés → **9 scrapers actifs** au total
- Dockerfile mis à jour avec `playwright install --with-deps chromium`
- Cleanup browser au shutdown worker

### Phase 6 — Notion Sync Bidirectionnel (terminé)
- **Push** (existant) : DB → Notion (jobs + companies)
- **Pull** (nouveau) : Notion → DB (statut + notes via `pull_notion_changes()`)
- Conflit : Notion gagne pour statut/notes, DB gagne pour score/keywords
- Migration 010 : `notion_last_sync_at` sur profiles
- Propriété "Notes" ajoutée au setup Notion
- 14 tests (mapping statut, properties, pull logic)

### Phase 7 — Tests 127+ (terminé)
- 61 → **127 tests** (+66 tests, +1200 lignes)
- 8 nouveaux fichiers de tests :
  - `test_admin.py` (7) — accès admin, users, metrics, scrapers
  - `test_billing.py` (7) — status, checkout, portal, webhooks Stripe
  - `test_stats.py` (7) — stats, charts, scrape-runs
  - `test_notifications.py` (7) — digest HTML, messages Telegram
  - `test_feedback.py` (5) — analyse keywords, préférences, stats
  - `test_scrapers.py` (17) — RawJob, retry, source names, config
  - `test_notion_sync.py` (14) — mapping statut, properties, pull
  - `test_worker.py` (+10) — email validation, mailto, notifications config

### Phase 8 — UX Mobile (terminé)
- `JobCard.tsx` : vue carte pour mobile (score, titre, entreprise, actions)
- `MobileNav.tsx` : hamburger menu + drawer sur mobile, liens inline sur desktop
- `FilterBar.tsx` : filtres collapsibles mobile, inline desktop, 10 sources
- `Badges.tsx` : composants partagés ScoreBadge/StatusBadge/RemoteBadge
- Dashboard responsive : table `md:+`, cards mobile `<md:`

### Phase 9 — Emails, Onboarding, Monitoring (terminé)
- **Emails transactionnels Brevo** (`worker/emails.py`) :
  - Welcome email après onboarding (avec tracking `welcome_email_sent_at`)
  - Weekly digest top 5 (1x/semaine, `last_digest_at` tracking)
  - Confirmation envoi candidature auto (intégré dans `auto_apply.py`)
  - Templates HTML inline, envoi via Brevo API
  - Migration 011 : `welcome_email_sent_at`, `last_digest_at` sur profiles
- **Tests d'intégration scrapers** (`tests/test_integration_scrapers.py`) :
  - 9 scrapers testés avec `@pytest.mark.integration`
  - Validation RawJob (title, company, source, source_url)
  - Tests contrat BaseScraper (source_name, scrape method)
  - Exclus par défaut (`pytest -m "not integration"`)
- **Onboarding amélioré** (`ProfileForm.tsx`) :
  - Indicateur temps estimé par étape ("Step 1/5 — ~1 min")
  - Validation temps réel (nom requis, CV min 50 chars, queries requises)
  - Extraction automatique de keywords depuis le CV (35 tech keywords)
  - Bouton "Use these as bonus keywords" pour appliquer les suggestions
  - Skip optionnel sur étapes 4 (Keywords) et 5 (Notifications)
  - Bordure rouge + message d'erreur sur champs invalides
- **Performance & Monitoring** :
  - `duration_seconds` par scraper dans `scrape_runs` (migration 012)
  - Sentry breadcrumbs : start/fail par scraper dans `tasks.py`
  - Endpoint `/api/scrape-runs/health` : taux de succès, durée moyenne, dernière erreur par source
  - Modèle `ScraperHealthMetrics` dans l'API
  - 13 nouveaux tests (`test_emails.py`)

---

## Prochaines étapes possibles

### Analytics avancées
- Dashboard graphique : évolution score/semaine, sources les plus productives
- Heatmap des heures de publication par source
- Taux de conversion par source (scraped → interested → applied)

### Multi-CV / Profils de recherche
- Plusieurs profils de recherche par utilisateur (ex: ML + Backend)
- CV différent par profil
- Scoring indépendant par profil

### Amélioration scraping
- Rotation de proxies pour éviter les bans
- Détection automatique CAPTCHA/Cloudflare avec fallback
- Scraper LinkedIn (via JobSpy amélioré)

### Déploiement & DevOps
- CI/CD GitHub Actions (ruff + pytest) sur PR
- Healthcheck endpoint pour Render auto-restart
- Backup automatique Supabase
