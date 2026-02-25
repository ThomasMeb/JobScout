-- Phase 6: Notion bidirectional sync
-- Add timestamp to track last pull from Notion per user
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS notion_last_sync_at TIMESTAMPTZ;
