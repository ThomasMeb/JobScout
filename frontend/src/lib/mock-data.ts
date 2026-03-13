import type { Profile, Job, JobListResponse, UserStats, ChartData, ScrapeRun } from "./types";

// ─── Profile ───────────────────────────────────────────────

export const MOCK_PROFILE: Profile = {
  id: "mock-user-001",
  name: "Thomas Mebarki",
  cv_text: "Data Scientist & Full-Stack Developer — Python, TypeScript, React, FastAPI, Machine Learning, NLP, Docker, Kubernetes. 5 ans d'expérience.",
  profile_summary: "Développeur full-stack orienté data avec expertise en ML/NLP. Recherche postes en data science ou ingénierie logicielle, idéalement en télétravail.",
  search_queries: ["data scientist", "full-stack developer", "machine learning engineer", "python developer"],
  search_locations: ["Paris", "Lyon", "Remote"],
  remote_accepted: true,
  min_salary: 55000,
  bonus_keywords: ["Python", "React", "TypeScript", "FastAPI", "Docker", "NLP", "LLM", "Kubernetes"],
  penalty_keywords: ["PHP", "Wordpress", "Salesforce", "SAP"],
  min_score_notify: 70,
  telegram_chat_id: null,
  notification_email: "thomas@mebarki.dev",
  monthly_budget_usd: 5,
  onboarding_completed: true,
  plan: "pro",
};

// ─── Jobs ──────────────────────────────────────────────────

const now = new Date();
function daysAgo(n: number) {
  const d = new Date(now);
  d.setDate(d.getDate() - n);
  return d.toISOString();
}

export const MOCK_JOBS: Job[] = [
  {
    id: 1, raw_job_id: 10001,
    title: "Senior Data Scientist — NLP & LLM",
    company: "Mistral AI",
    location: "Paris 2e",
    remote_type: "hybrid",
    salary_min: 75000, salary_max: 95000, salary_currency: "EUR",
    source: "wttj", source_url: "https://www.welcometothejungle.com/fr/companies/mistral-ai",
    apply_url: "https://www.welcometothejungle.com/fr/companies/mistral-ai/jobs/senior-data-scientist",
    tags: ["Python", "NLP", "LLM", "PyTorch", "Transformers"],
    match_score: 94, match_reasoning: "Excellente correspondance : expertise NLP/LLM demandée, stack Python/PyTorch aligné, salaire dans la fourchette haute. Localisation Paris + hybrid convient.",
    match_keywords: ["Python", "NLP", "LLM", "PyTorch"], missing_keywords: ["Rust"],
    match_priority: "high", status: "new", user_notes: null,
    posted_at: daysAgo(1), scored_at: daysAgo(0),
  },
  {
    id: 2, raw_job_id: 10002,
    title: "Full-Stack Engineer (React + Python)",
    company: "Alan",
    location: "Paris 9e",
    remote_type: "full_remote",
    salary_min: 60000, salary_max: 80000, salary_currency: "EUR",
    source: "wttj", source_url: "https://www.welcometothejungle.com/fr/companies/alan",
    apply_url: null,
    tags: ["React", "TypeScript", "Python", "FastAPI", "PostgreSQL", "Docker"],
    match_score: 91, match_reasoning: "Stack parfaitement aligné : React + TypeScript + Python + FastAPI. Full remote accepté. Culture tech forte chez Alan.",
    match_keywords: ["React", "TypeScript", "Python", "FastAPI", "Docker"], missing_keywords: ["Go"],
    match_priority: "high", status: "interested", user_notes: "Super culture tech, à creuser",
    posted_at: daysAgo(2), scored_at: daysAgo(1),
  },
  {
    id: 3, raw_job_id: 10003,
    title: "ML Engineer — Computer Vision",
    company: "Photoroom",
    location: "Paris 11e",
    remote_type: "hybrid",
    salary_min: 65000, salary_max: 85000, salary_currency: "EUR",
    source: "remoteok", source_url: "https://remoteok.com/jobs/12345",
    apply_url: "https://remoteok.com/jobs/12345/apply",
    tags: ["Python", "PyTorch", "Computer Vision", "MLOps", "AWS"],
    match_score: 82, match_reasoning: "Bonne correspondance ML, mais orientation Computer Vision alors que le profil est plus NLP. Stack Python/PyTorch OK.",
    match_keywords: ["Python", "PyTorch", "MLOps"], missing_keywords: ["Computer Vision", "OpenCV"],
    match_priority: "medium", status: "new", user_notes: null,
    posted_at: daysAgo(1), scored_at: daysAgo(0),
  },
  {
    id: 4, raw_job_id: 10004,
    title: "Lead Développeur Python",
    company: "BlaBlaCar",
    location: "Paris 17e",
    remote_type: "hybrid",
    salary_min: 70000, salary_max: 90000, salary_currency: "EUR",
    source: "francetravail", source_url: "https://candidat.francetravail.fr/offres/123456",
    apply_url: null,
    tags: ["Python", "Django", "PostgreSQL", "Redis", "Kubernetes", "CI/CD"],
    match_score: 78, match_reasoning: "Python et Kubernetes alignés. Django au lieu de FastAPI, mais transférable. Rôle Lead intéressant pour l'évolution.",
    match_keywords: ["Python", "PostgreSQL", "Kubernetes"], missing_keywords: ["Django"],
    match_priority: "medium", status: "new", user_notes: null,
    posted_at: daysAgo(3), scored_at: daysAgo(2),
  },
  {
    id: 5, raw_job_id: 10005,
    title: "Data Engineer — Pipeline & Analytics",
    company: "Doctolib",
    location: "Paris 10e",
    remote_type: "hybrid",
    salary_min: 55000, salary_max: 72000, salary_currency: "EUR",
    source: "adzuna", source_url: "https://www.adzuna.fr/details/12345",
    apply_url: "https://careers.doctolib.com/data-engineer",
    tags: ["Python", "Spark", "Airflow", "dbt", "BigQuery", "Terraform"],
    match_score: 71, match_reasoning: "Profil Data Engineer plutôt que Data Scientist, mais compétences Python transférables. Doctolib est un excellent environnement tech.",
    match_keywords: ["Python", "Terraform"], missing_keywords: ["Spark", "Airflow", "dbt"],
    match_priority: "medium", status: "applied", user_notes: "Candidature envoyée le 10/03, relance prévue le 17/03",
    posted_at: daysAgo(5), scored_at: daysAgo(4),
  },
  {
    id: 6, raw_job_id: 10006,
    title: "Développeur Frontend React Senior",
    company: "Qonto",
    location: "Paris 2e",
    remote_type: "full_remote",
    salary_min: 58000, salary_max: 75000, salary_currency: "EUR",
    source: "wttj", source_url: "https://www.welcometothejungle.com/fr/companies/qonto",
    apply_url: null,
    tags: ["React", "TypeScript", "Next.js", "GraphQL", "Storybook", "Jest"],
    match_score: 68, match_reasoning: "React/TypeScript/Next.js alignés, mais rôle purement frontend. Pas de Python ni ML. Full remote est un plus.",
    match_keywords: ["React", "TypeScript", "Next.js"], missing_keywords: ["GraphQL", "Storybook"],
    match_priority: "medium", status: "new", user_notes: null,
    posted_at: daysAgo(2), scored_at: daysAgo(1),
  },
  {
    id: 7, raw_job_id: 10007,
    title: "MLOps Engineer",
    company: "Datadog",
    location: "Paris 9e",
    remote_type: "hybrid",
    salary_min: 70000, salary_max: 100000, salary_currency: "EUR",
    source: "hellowork", source_url: "https://www.hellowork.com/fr-fr/emplois/12345",
    apply_url: "https://careers.datadoghq.com/mlops",
    tags: ["Python", "Kubernetes", "Docker", "MLflow", "AWS", "Terraform"],
    match_score: 85, match_reasoning: "MLOps correspond bien au profil ML + infra. Kubernetes et Docker maîtrisés. Datadog = entreprise de référence en observabilité.",
    match_keywords: ["Python", "Kubernetes", "Docker"], missing_keywords: ["MLflow"],
    match_priority: "high", status: "interested", user_notes: "Demander à Pierre s'il connaît du monde là-bas",
    posted_at: daysAgo(1), scored_at: daysAgo(0),
  },
  {
    id: 8, raw_job_id: 10008,
    title: "Développeur PHP/Symfony",
    company: "Capgemini",
    location: "La Défense",
    remote_type: "on_site",
    salary_min: 40000, salary_max: 50000, salary_currency: "EUR",
    source: "francetravail", source_url: "https://candidat.francetravail.fr/offres/234567",
    apply_url: null,
    tags: ["PHP", "Symfony", "MySQL", "jQuery"],
    match_score: 15, match_reasoning: "PHP est un penalty keyword. Pas de Python ni ML. On-site uniquement. Salaire en dessous du minimum.",
    match_keywords: [], missing_keywords: ["PHP", "Symfony"],
    match_priority: "low", status: "rejected", user_notes: "Pas du tout mon profil",
    posted_at: daysAgo(4), scored_at: daysAgo(3),
  },
  {
    id: 9, raw_job_id: 10009,
    title: "AI Research Scientist — Reinforcement Learning",
    company: "Hugging Face",
    location: "Paris 3e",
    remote_type: "full_remote",
    salary_min: 80000, salary_max: 120000, salary_currency: "EUR",
    source: "remoteok", source_url: "https://remoteok.com/jobs/67890",
    apply_url: "https://apply.workable.com/huggingface/",
    tags: ["Python", "PyTorch", "Reinforcement Learning", "Transformers", "Research"],
    match_score: 88, match_reasoning: "Hugging Face = entreprise idéale pour profil ML/NLP. Stack Python/PyTorch aligné. Full remote. RL est un domaine adjacent.",
    match_keywords: ["Python", "PyTorch", "Transformers"], missing_keywords: ["Reinforcement Learning", "Publications"],
    match_priority: "high", status: "applied", user_notes: "Entretien technique prévu semaine prochaine !",
    posted_at: daysAgo(7), scored_at: daysAgo(6),
  },
  {
    id: 10, raw_job_id: 10010,
    title: "Backend Developer Node.js",
    company: "Swile",
    location: "Montpellier",
    remote_type: "hybrid",
    salary_min: 50000, salary_max: 65000, salary_currency: "EUR",
    source: "wttj", source_url: "https://www.welcometothejungle.com/fr/companies/swile",
    apply_url: null,
    tags: ["Node.js", "TypeScript", "PostgreSQL", "Redis", "RabbitMQ"],
    match_score: 52, match_reasoning: "TypeScript connu mais rôle Node.js backend sans Python ni ML. Montpellier hors localisation préférée.",
    match_keywords: ["TypeScript", "PostgreSQL"], missing_keywords: ["Node.js", "RabbitMQ"],
    match_priority: "low", status: "new", user_notes: null,
    posted_at: daysAgo(3), scored_at: daysAgo(2),
  },
  {
    id: 11, raw_job_id: 10011,
    title: "Data Scientist Junior — Santé",
    company: "Owkin",
    location: "Paris 13e",
    remote_type: "hybrid",
    salary_min: 42000, salary_max: 52000, salary_currency: "EUR",
    source: "apec", source_url: "https://www.apec.fr/candidat/offres/12345",
    apply_url: "https://owkin.com/careers",
    tags: ["Python", "Scikit-learn", "Deep Learning", "Biology", "Research"],
    match_score: 61, match_reasoning: "Data Science mais profil junior et domaine santé/bio spécialisé. Salaire sous le minimum. Python OK.",
    match_keywords: ["Python", "Deep Learning"], missing_keywords: ["Biology", "Research"],
    match_priority: "low", status: "new", user_notes: null,
    posted_at: daysAgo(6), scored_at: daysAgo(5),
  },
  {
    id: 12, raw_job_id: 10012,
    title: "Tech Lead Full-Stack — Scale-up FinTech",
    company: "Pennylane",
    location: "Paris 9e",
    remote_type: "hybrid",
    salary_min: 75000, salary_max: 95000, salary_currency: "EUR",
    source: "freework", source_url: "https://www.free-work.com/fr/tech-it/emploi/12345",
    apply_url: "https://www.pennylane.com/careers",
    tags: ["React", "TypeScript", "Ruby on Rails", "PostgreSQL", "AWS", "Terraform"],
    match_score: 73, match_reasoning: "React/TypeScript alignés, mais Ruby on Rails demandé. Rôle Tech Lead intéressant. Pennylane en forte croissance.",
    match_keywords: ["React", "TypeScript", "PostgreSQL", "AWS"], missing_keywords: ["Ruby on Rails"],
    match_priority: "medium", status: "new", user_notes: null,
    posted_at: daysAgo(2), scored_at: daysAgo(1),
  },
  {
    id: 13, raw_job_id: 10013,
    title: "Ingénieur Machine Learning — NLP",
    company: "Luko (ex-Lemonade)",
    location: "Paris 10e",
    remote_type: "full_remote",
    salary_min: 60000, salary_max: 80000, salary_currency: "EUR",
    source: "welovedevs", source_url: "https://welovedevs.com/app/offre/12345",
    apply_url: "https://jobs.lever.co/luko/12345",
    tags: ["Python", "NLP", "spaCy", "Transformers", "FastAPI", "Docker"],
    match_score: 92, match_reasoning: "Match quasi parfait : NLP + Python + FastAPI + Docker. Full remote. L'assurance est un secteur en pleine transformation IA.",
    match_keywords: ["Python", "NLP", "Transformers", "FastAPI", "Docker"], missing_keywords: ["spaCy"],
    match_priority: "high", status: "interested", user_notes: "Très bon match, préparer portfolio NLP",
    posted_at: daysAgo(1), scored_at: daysAgo(0),
  },
  {
    id: 14, raw_job_id: 10014,
    title: "Consultant Data & IA",
    company: "Accenture",
    location: "Paris La Défense",
    remote_type: "on_site",
    salary_min: 45000, salary_max: 60000, salary_currency: "EUR",
    source: "francetravail", source_url: "https://candidat.francetravail.fr/offres/345678",
    apply_url: null,
    tags: ["Python", "SQL", "PowerBI", "Azure", "Consulting"],
    match_score: 35, match_reasoning: "Rôle consulting, pas de dev. PowerBI et Azure pas dans les compétences. On-site La Défense. Salaire bas.",
    match_keywords: ["Python", "SQL"], missing_keywords: ["PowerBI", "Azure", "Consulting"],
    match_priority: "low", status: "rejected", user_notes: null,
    posted_at: daysAgo(5), scored_at: daysAgo(4),
  },
  {
    id: 15, raw_job_id: 10015,
    title: "DevOps / SRE — Kubernetes Expert",
    company: "OVHcloud",
    location: "Roubaix",
    remote_type: "hybrid",
    salary_min: 55000, salary_max: 75000, salary_currency: "EUR",
    source: "adzuna", source_url: "https://www.adzuna.fr/details/67890",
    apply_url: "https://careers.ovhcloud.com/devops-sre",
    tags: ["Kubernetes", "Docker", "Terraform", "Go", "Prometheus", "Grafana"],
    match_score: 58, match_reasoning: "Kubernetes et Docker connus mais rôle SRE pur sans ML. Go demandé. Roubaix hors localisation.",
    match_keywords: ["Kubernetes", "Docker", "Terraform"], missing_keywords: ["Go", "Prometheus"],
    match_priority: "low", status: "new", user_notes: null,
    posted_at: daysAgo(4), scored_at: daysAgo(3),
  },
];

// ─── Stats ─────────────────────────────────────────────────

export const MOCK_STATS: UserStats = {
  total_jobs: 247,
  new_jobs: 18,
  interested: 12,
  applied: 8,
  rejected: 23,
  avg_score: 67.4,
  monthly_cost_usd: 2.30,
  budget_remaining_usd: 2.70,
};

// ─── Chart Data ────────────────────────────────────────────

export const MOCK_CHART_DATA: ChartData = {
  score_buckets: {
    "0-20": 14,
    "20-40": 31,
    "40-60": 58,
    "60-80": 89,
    "80-100": 55,
  },
  daily_jobs: [
    { date: daysAgo(13), count: 12 },
    { date: daysAgo(12), count: 8 },
    { date: daysAgo(11), count: 22 },
    { date: daysAgo(10), count: 15 },
    { date: daysAgo(9), count: 31 },
    { date: daysAgo(8), count: 19 },
    { date: daysAgo(7), count: 27 },
    { date: daysAgo(6), count: 14 },
    { date: daysAgo(5), count: 35 },
    { date: daysAgo(4), count: 21 },
    { date: daysAgo(3), count: 28 },
    { date: daysAgo(2), count: 17 },
    { date: daysAgo(1), count: 33 },
    { date: daysAgo(0), count: 18 },
  ],
};

// ─── Scrape Runs ───────────────────────────────────────────

export const MOCK_SCRAPE_RUNS: ScrapeRun[] = [
  { id: 1, source: "wttj", jobs_found: 45, jobs_new: 8, status: "success", error_message: null, started_at: daysAgo(0), finished_at: daysAgo(0) },
  { id: 2, source: "remoteok", jobs_found: 23, jobs_new: 5, status: "success", error_message: null, started_at: daysAgo(0), finished_at: daysAgo(0) },
  { id: 3, source: "adzuna", jobs_found: 67, jobs_new: 12, status: "success", error_message: null, started_at: daysAgo(0), finished_at: daysAgo(0) },
  { id: 4, source: "francetravail", jobs_found: 89, jobs_new: 15, status: "success", error_message: null, started_at: daysAgo(0), finished_at: daysAgo(0) },
  { id: 5, source: "hellowork", jobs_found: 34, jobs_new: 6, status: "success", error_message: null, started_at: daysAgo(0), finished_at: daysAgo(0) },
  { id: 6, source: "apec", jobs_found: 28, jobs_new: 4, status: "success", error_message: null, started_at: daysAgo(0), finished_at: daysAgo(0) },
  { id: 7, source: "freework", jobs_found: 19, jobs_new: 3, status: "success", error_message: null, started_at: daysAgo(0), finished_at: daysAgo(0) },
  { id: 8, source: "welovedevs", jobs_found: 12, jobs_new: 2, status: "error", error_message: "Timeout after 30s — retrying next cycle", started_at: daysAgo(0), finished_at: null },
  { id: 9, source: "jobspy", jobs_found: 52, jobs_new: 9, status: "success", error_message: null, started_at: daysAgo(0), finished_at: daysAgo(0) },
];

// ─── Billing ───────────────────────────────────────────────

export const MOCK_BILLING = {
  plan: "pro",
  status: "active",
  trial_end: null,
  current_period_end: new Date(now.getFullYear(), now.getMonth() + 1, now.getDate()).toISOString(),
  cancel_at_period_end: false,
};

// ─── Admin ─────────────────────────────────────────────────

export const MOCK_ADMIN_USERS = [
  { id: "u1", name: "Thomas Mebarki", email: "thomas@mebarki.dev", plan: "pro", total_jobs: 247, onboarding_completed: true, created_at: "2026-01-15T10:00:00Z" },
  { id: "u2", name: "Marie Dupont", email: "marie.dupont@gmail.com", plan: "free", total_jobs: 34, onboarding_completed: true, created_at: "2026-02-20T14:30:00Z" },
  { id: "u3", name: "Lucas Martin", email: "lucas.martin@outlook.fr", plan: "pro", total_jobs: 189, onboarding_completed: true, created_at: "2026-01-28T09:15:00Z" },
  { id: "u4", name: "Sophie Bernard", email: "s.bernard@icloud.com", plan: "trial", total_jobs: 12, onboarding_completed: false, created_at: "2026-03-10T16:45:00Z" },
  { id: "u5", name: "Ahmed Benali", email: "a.benali@proton.me", plan: "pro", total_jobs: 156, onboarding_completed: true, created_at: "2026-02-05T11:20:00Z" },
];

export const MOCK_ADMIN_METRICS = {
  total_users: 5,
  pro_users: 3,
  raw_jobs: 1247,
  scored_jobs: 1089,
  worker_status: "running",
  cycles: 342,
};

export const MOCK_ADMIN_SCRAPERS = MOCK_SCRAPE_RUNS.filter((r) => r.status === "success").map((r) => ({
  source: r.source,
  runs: Math.floor(Math.random() * 100) + 50,
  success_rate: r.status === "success" ? 0.95 + Math.random() * 0.05 : 0.7,
  jobs_found: r.jobs_found * 10,
  jobs_new: r.jobs_new * 10,
  last_run: r.started_at,
  errors: 0,
}));

// ─── Mock API helper ──────────────────────────────────────

export function isMockMode(): boolean {
  if (process.env.NEXT_PUBLIC_MOCK_MODE === "true") return true;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  return !url || url === "https://placeholder.supabase.co";
}

export function getMockJobs(filters: {
  page?: number;
  per_page?: number;
  min_score?: number;
  status?: string;
  source?: string;
  search?: string;
} = {}): JobListResponse {
  let filtered = [...MOCK_JOBS];

  if (filters.min_score) {
    filtered = filtered.filter((j) => (j.match_score ?? 0) >= filters.min_score!);
  }
  if (filters.status) {
    filtered = filtered.filter((j) => j.status === filters.status);
  }
  if (filters.source) {
    filtered = filtered.filter((j) => j.source === filters.source);
  }
  if (filters.search) {
    const q = filters.search.toLowerCase();
    filtered = filtered.filter(
      (j) =>
        j.title.toLowerCase().includes(q) ||
        j.company.toLowerCase().includes(q) ||
        j.tags.some((t) => t.toLowerCase().includes(q))
    );
  }

  // Sort by score descending
  filtered.sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0));

  const page = filters.page ?? 1;
  const perPage = filters.per_page ?? 20;
  const start = (page - 1) * perPage;
  const paged = filtered.slice(start, start + perPage);

  return {
    jobs: paged,
    total: filtered.length,
    page,
    per_page: perPage,
  };
}
