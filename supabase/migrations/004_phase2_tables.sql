-- Phase 2: Applications tracking + Companies CRM + Notion integration
-- Run after 001, 002, 003 migrations

-- Table: applications (per-user candidature tracking)
CREATE TABLE public.applications (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    user_job_id BIGINT NOT NULL REFERENCES public.user_jobs(id) ON DELETE CASCADE,
    cv_storage_path TEXT,
    cover_letter TEXT,
    linkedin_tips TEXT,
    language TEXT DEFAULT 'fr',
    status TEXT DEFAULT 'draft',
    cost_usd NUMERIC(10,6) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    validated_at TIMESTAMPTZ,
    UNIQUE(user_id, user_job_id)
);

CREATE INDEX idx_applications_user_id ON public.applications(user_id);
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;
CREATE POLICY applications_select ON public.applications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY applications_update ON public.applications FOR UPDATE USING (auth.uid() = user_id);

-- Table: companies (per-user target companies)
CREATE TABLE public.companies (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    website TEXT,
    careers_url TEXT,
    sector TEXT,
    location TEXT,
    source TEXT DEFAULT 'manual',
    relevance_score REAL DEFAULT 0,
    spontaneous_status TEXT DEFAULT 'pending',
    notion_page_id TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, name, source)
);

CREATE INDEX idx_companies_user_id ON public.companies(user_id);
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
CREATE POLICY companies_select ON public.companies FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY companies_update ON public.companies FOR UPDATE USING (auth.uid() = user_id);

-- Add Notion columns to existing tables
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS notion_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE public.user_jobs ADD COLUMN IF NOT EXISTS notion_page_id TEXT;
