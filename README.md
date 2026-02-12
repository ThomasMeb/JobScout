# 🔍 JobScout — AI-Powered Job Search Automation

> Autonomous agent that scrapes, scores, and tracks job opportunities using LLM-based profile matching.

**Scrape 5+ sources → Score with AI → Get notified on Telegram → Track in Notion**

---

## Features

- **Multi-source scraping** — Welcome to the Jungle, Adzuna, France Travail, RemoteOK, JobSpy (Indeed/LinkedIn/Glassdoor)
- **AI-powered scoring** — DeepSeek LLM scores each job 0-100 against your profile with detailed reasoning
- **Telegram notifications** — Real-time alerts with action buttons (Interested / Reject / Prepare application)
- **Notion sync** — Automatically pushes scored jobs and target companies to your Notion workspace
- **Company research** — La Bonne Boite API + manual target list for spontaneous applications
- **Application briefs** — Auto-generated preparation dossiers for high-scoring opportunities
- **Dashboard** — Streamlit visualization of your job search data
- **Budget control** — Monthly LLM cost tracking with configurable limits

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  5 Scrapers  │────▶│  SQLite DB   │────▶│   Telegram   │
│  (async)     │     │  (WAL mode)  │     │  Bot + Notif │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────▼───────┐     ┌──────────────┐
                    │  DeepSeek    │     │    Notion     │
                    │  LLM Scoring │     │    Sync       │
                    └──────────────┘     └──────────────┘
                                         ┌──────────────┐
                                         │  Streamlit   │
                                         │  Dashboard   │
                                         └──────────────┘
```

### Pipeline (every 6h, 7am-11pm)

1. **Scrape** — Fetch jobs from all enabled sources
2. **Deduplicate** — SHA256 hash on title + company + URL
3. **Score** — LLM evaluates job-profile fit (0-100) with reasoning, keywords, priority
4. **Notify** — Telegram messages with inline action buttons for jobs above threshold
5. **Company research** — Find companies via La Bonne Boite + manual targets
6. **Notion sync** — Push scored jobs and companies to Notion databases

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/ThomasMeb/JobScout.git
cd JobScout
pip install -r requirements.txt
```

### 2. Configure your profile

Edit `config.yaml` to match your job search:

```yaml
profile:
  name: "Your Name"
  profile_doc: |
    3 years Python, ML/DL, NLP...
    Looking for: ML Engineer, Data Scientist
    Location: Paris, Remote OK

search:
  queries:
    - "ML Engineer"
    - "Data Scientist"
    - "AI Engineer"
  locations:
    - "Paris"
    - "London"
  remote_accepted: true
  contract_types: ["CDI", "full-time"]
  min_salary: 45000

scoring:
  min_score_notify: 60        # Telegram notification threshold
  bonus_keywords: [python, pytorch, mlops, docker]
  penalty_keywords: [10+ years, PhD required, Java]
```

### 3. Create API keys

Copy the template and fill in your keys:

```bash
cp .env.example .env
```

| Service | Where to get it | Required |
|---------|----------------|----------|
| **DeepSeek** | [platform.deepseek.com](https://platform.deepseek.com) | Yes |
| **Telegram Bot** | Talk to [@BotFather](https://t.me/BotFather) on Telegram | Yes |
| **Adzuna** | [developer.adzuna.com](https://developer.adzuna.com) | Recommended |
| **France Travail** | [francetravail.io](https://francetravail.io) | Optional |
| **Notion** | [notion.so/my-integrations](https://www.notion.so/my-integrations) | Optional |

**Telegram Chat ID**: Send `/start` to your bot, then run:
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

### 4. Run

```bash
# Single cycle (scrape + score + notify)
python main.py --once

# Daemon mode (runs every 6h with Telegram bot listener)
python main.py

# Dashboard
streamlit run dashboard.py
```

## Configuration Reference

### Sources

Enable/disable scrapers in `config.yaml`:

```yaml
sources:
  wttj:
    enabled: true          # Welcome to the Jungle
  adzuna:
    enabled: true          # Adzuna API (needs API key)
  francetravail:
    enabled: true          # France Travail API
  remoteok:
    enabled: true          # RemoteOK (no key needed)
  jobspy:
    enabled: true          # Indeed + LinkedIn + Glassdoor
  hellowork:
    enabled: false         # Requires Playwright (SPA)
```

### Target Companies

Add companies for spontaneous applications:

```yaml
target_companies:
  - name: "Mistral AI"
    website: "https://mistral.ai"
    careers_url: "https://mistral.ai/careers"
    sector: "LLM / AI Research"
    location: "Paris"
    relevance_score: 95
```

### Notion Integration

1. Create an integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create two databases: **Jobs** and **Companies**
3. Connect your integration to both databases
4. Add the tokens to `.env`

The agent auto-creates all required properties on first sync.

### Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize the bot |
| `/status` | Global statistics |
| `/pending` | Jobs waiting for review |
| `/companies` | Target companies list |
| `/costs` | LLM spending this month |
| `/pause` | Pause the scheduler |
| `/resume` | Resume the scheduler |

### Daemon (systemd)

```bash
# Create service
mkdir -p ~/.config/systemd/user
cp jobscout.service ~/.config/systemd/user/

# Enable and start
systemctl --user daemon-reload
systemctl --user enable --now jobscout

# Logs
journalctl --user -u jobscout -f
```

## Costs

DeepSeek pricing makes this very affordable:

| Items | Cost | Time |
|-------|------|------|
| 1,300 jobs scored | ~$1.00 | ~2 hours |
| Monthly (4 cycles/day) | ~$3-5 | Automatic |

Budget is configurable and enforced — the agent stops scoring when the monthly limit is reached.

## Project Structure

```
JobScout/
├── main.py                    # CLI entry point (--once / daemon)
├── dashboard.py               # Streamlit dashboard
├── config.yaml                # All configuration
├── .env.example               # API keys template
│
├── job_agent/
│   ├── config.py              # Config loader
│   ├── storage.py             # SQLite schema + CRUD
│   ├── llm.py                 # DeepSeek async client
│   ├── matcher.py             # LLM-based job scoring
│   ├── notifier.py            # Telegram bot + notifications
│   ├── scheduler.py           # Pipeline orchestration
│   ├── company_research.py    # La Bonne Boite + targets
│   ├── application_prep.py    # Brief generator
│   ├── notion_sync.py         # Notion API sync
│   └── scrapers/              # 10 scrapers (5 active)
│       ├── base.py            # BaseScraper ABC
│       ├── wttj.py            # Welcome to the Jungle
│       ├── adzuna.py          # Adzuna API
│       ├── francetravail.py   # France Travail API
│       ├── remoteok.py        # RemoteOK
│       └── jobspy.py          # JobSpy (multi-source)
│
└── data/                      # SQLite DB + generated briefs (gitignored)
```

## License

MIT — See [LICENSE](LICENSE)
