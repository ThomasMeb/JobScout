# JobScout — Roadmap

> **127 tests** | 17 routes frontend | **9 scrapers actifs** | Stripe billing | Admin dashboard | Notion bidi | Mobile responsive
> Dernière mise à jour : 25 fév 2026

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

---

## Prochaines étapes possibles

### Emails transactionnels (Brevo)
- Welcome email après onboarding
- Weekly digest (top 5 jobs de la semaine)
- Confirmation envoi candidature auto
- Templates HTML dans `worker/emails.py`

### Onboarding amélioré
- Indicateur de temps estimé ("~3 min")
- Validation en temps réel
- Suggestions keywords basées sur le CV
- Skip optionnel des étapes non essentielles

### Scrapers Playwright — Tests d'intégration
- Tests réels marqués `@pytest.mark.integration`
- Vérifier que chaque scraper retourne des RawJob valides
- Monitoring CAPTCHA/Cloudflare

### Performance & Monitoring
- Dashboard Sentry : alerting sur erreurs scraper
- Métriques : temps de scrape par source, taux de succès
- Cache Redis pour les requêtes API fréquentes
