export interface Profile {
  id: string;
  name: string | null;
  cv_text: string | null;
  profile_summary: string | null;
  search_queries: string[];
  search_locations: string[];
  remote_accepted: boolean;
  min_salary: number | null;
  bonus_keywords: string[];
  penalty_keywords: string[];
  min_score_notify: number;
  telegram_chat_id: string | null;
  notification_email: string | null;
  monthly_budget_usd: number;
  onboarding_completed: boolean;
  plan: string;
}

export interface Job {
  id: number;
  raw_job_id: number;
  title: string;
  company: string;
  location: string | null;
  remote_type: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  source: string;
  source_url: string;
  apply_url: string | null;
  tags: string[];
  match_score: number | null;
  match_reasoning: string | null;
  match_keywords: string[];
  missing_keywords: string[];
  match_priority: string;
  status: string;
  user_notes: string | null;
  posted_at: string | null;
  scored_at: string | null;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  per_page: number;
}

export interface ScrapeRun {
  id: number;
  source: string;
  jobs_found: number;
  jobs_new: number;
  status: string;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface DailyCount {
  date: string;
  count: number;
}

export interface ChartData {
  score_buckets: Record<string, number>;
  daily_jobs: DailyCount[];
}

export interface UserStats {
  total_jobs: number;
  new_jobs: number;
  interested: number;
  applied: number;
  rejected: number;
  avg_score: number | null;
  monthly_cost_usd: number;
  budget_remaining_usd: number;
}
