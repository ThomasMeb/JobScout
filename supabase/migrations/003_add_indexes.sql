-- Composite index for dashboard queries (filter by user + status)
CREATE INDEX IF NOT EXISTS idx_user_jobs_user_status
    ON public.user_jobs(user_id, status);

-- Index for notification queries (unnotified jobs above threshold)
CREATE INDEX IF NOT EXISTS idx_user_jobs_user_notified
    ON public.user_jobs(user_id, notified_at)
    WHERE notified_at IS NULL;
