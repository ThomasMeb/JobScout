-- Phase 9: Email tracking columns for transactional emails
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS welcome_email_sent_at TIMESTAMPTZ;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS last_digest_at TIMESTAMPTZ;
