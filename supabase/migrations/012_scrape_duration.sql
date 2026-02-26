-- Phase 9: Add duration tracking to scrape_runs
ALTER TABLE scrape_runs ADD COLUMN IF NOT EXISTS duration_seconds REAL;
