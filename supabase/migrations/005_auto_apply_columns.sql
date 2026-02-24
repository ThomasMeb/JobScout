-- Auto-apply: add sent tracking columns to applications table
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS sent_to_email TEXT;
