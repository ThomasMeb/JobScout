-- JobScout SaaS - Initial Schema
-- Extends Supabase auth.users with multi-tenant job matching

-- ============================================================
-- PROFILES (extends auth.users)
-- ============================================================
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT,
    cv_text TEXT,
    profile_summary TEXT,
    search_queries TEXT[] DEFAULT '{}',
    search_locations TEXT[] DEFAULT '{}',
    remote_accepted BOOLEAN DEFAULT TRUE,
    min_salary INTEGER,
    bonus_keywords TEXT[] DEFAULT '{}',
    penalty_keywords TEXT[] DEFAULT '{}',
    min_score_notify INTEGER DEFAULT 70,
    telegram_chat_id TEXT,
    notification_email TEXT,
    monthly_budget_usd NUMERIC(6,2) DEFAULT 5.00,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, notification_email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- ============================================================
-- RAW_JOBS (global pool, scraped once for all users)
-- ============================================================
CREATE TABLE public.raw_jobs (
    id BIGSERIAL PRIMARY KEY,
    hash TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    remote_type TEXT DEFAULT 'unknown',
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT DEFAULT 'EUR',
    description TEXT,
    tags JSONB DEFAULT '[]',
    source TEXT NOT NULL,
    source_url TEXT NOT NULL,
    apply_url TEXT,
    company_url TEXT,
    posted_at TIMESTAMPTZ,
    scraped_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_raw_jobs_hash ON public.raw_jobs(hash);
CREATE INDEX idx_raw_jobs_source ON public.raw_jobs(source);
CREATE INDEX idx_raw_jobs_scraped_at ON public.raw_jobs(scraped_at);
CREATE INDEX idx_raw_jobs_posted_at ON public.raw_jobs(posted_at);

-- ============================================================
-- USER_JOBS (per-user scored jobs)
-- ============================================================
CREATE TABLE public.user_jobs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    raw_job_id BIGINT NOT NULL REFERENCES public.raw_jobs(id) ON DELETE CASCADE,
    match_score REAL,
    match_reasoning TEXT,
    match_keywords JSONB DEFAULT '[]',
    missing_keywords JSONB DEFAULT '[]',
    match_priority TEXT DEFAULT 'low',
    status TEXT DEFAULT 'new',
    user_notes TEXT,
    notified_at TIMESTAMPTZ,
    scored_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, raw_job_id)
);

CREATE INDEX idx_user_jobs_user_id ON public.user_jobs(user_id);
CREATE INDEX idx_user_jobs_score ON public.user_jobs(match_score);
CREATE INDEX idx_user_jobs_status ON public.user_jobs(status);

CREATE TRIGGER user_jobs_updated_at
    BEFORE UPDATE ON public.user_jobs
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- ============================================================
-- LLM_USAGE (per-user cost tracking)
-- ============================================================
CREATE TABLE public.llm_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    operation TEXT NOT NULL,
    user_job_id BIGINT REFERENCES public.user_jobs(id) ON DELETE SET NULL,
    model TEXT DEFAULT 'deepseek-chat',
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    cost_usd NUMERIC(10,6) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_llm_usage_user_id ON public.llm_usage(user_id);
CREATE INDEX idx_llm_usage_created_at ON public.llm_usage(created_at);

-- ============================================================
-- SCRAPE_RUNS (global, tracking scraper health)
-- ============================================================
CREATE TABLE public.scrape_runs (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    jobs_found INTEGER DEFAULT 0,
    jobs_new INTEGER DEFAULT 0,
    queries_used JSONB DEFAULT '[]',
    status TEXT DEFAULT 'running',
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX idx_scrape_runs_source ON public.scrape_runs(source);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- Profiles: users can only read/update their own
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY profiles_select ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY profiles_update ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Raw jobs: any authenticated user can read
ALTER TABLE public.raw_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY raw_jobs_select ON public.raw_jobs
    FOR SELECT USING (auth.role() = 'authenticated');

-- User jobs: users can only access their own
ALTER TABLE public.user_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_jobs_select ON public.user_jobs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY user_jobs_update ON public.user_jobs
    FOR UPDATE USING (auth.uid() = user_id);

-- LLM usage: users can only see their own
ALTER TABLE public.llm_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY llm_usage_select ON public.llm_usage
    FOR SELECT USING (auth.uid() = user_id);

-- Scrape runs: any authenticated user can read
ALTER TABLE public.scrape_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY scrape_runs_select ON public.scrape_runs
    FOR SELECT USING (auth.role() = 'authenticated');
