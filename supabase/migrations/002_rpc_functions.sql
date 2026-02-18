-- JobScout SaaS - RPC Functions for Worker
-- Used by the worker to efficiently find unscored jobs per user.

-- ============================================================
-- get_unscored_jobs_for_user
-- Returns raw_jobs from last N days that are NOT yet in user_jobs
-- for the given user, optionally filtered by query/location match.
-- ============================================================
CREATE OR REPLACE FUNCTION public.get_unscored_jobs_for_user(
    p_user_id UUID,
    p_queries TEXT[] DEFAULT '{}',
    p_locations TEXT[] DEFAULT '{}',
    p_days_back INTEGER DEFAULT 7,
    p_limit INTEGER DEFAULT 100
)
RETURNS SETOF public.raw_jobs
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT rj.*
    FROM public.raw_jobs rj
    WHERE
        -- Only recent jobs
        rj.scraped_at >= NOW() - (p_days_back || ' days')::INTERVAL
        -- Not already scored for this user
        AND NOT EXISTS (
            SELECT 1 FROM public.user_jobs uj
            WHERE uj.raw_job_id = rj.id AND uj.user_id = p_user_id
        )
        -- Match at least one query (case-insensitive title search)
        -- If no queries provided, match all jobs
        AND (
            array_length(p_queries, 1) IS NULL
            OR EXISTS (
                SELECT 1 FROM unnest(p_queries) q
                WHERE rj.title ILIKE '%' || q || '%'
                   OR rj.description ILIKE '%' || q || '%'
            )
        )
        -- Match at least one location (if provided)
        AND (
            array_length(p_locations, 1) IS NULL
            OR rj.location IS NULL
            OR EXISTS (
                SELECT 1 FROM unnest(p_locations) loc
                WHERE rj.location ILIKE '%' || loc || '%'
            )
            OR rj.remote_type = 'full'
        )
    ORDER BY rj.scraped_at DESC
    LIMIT p_limit;
$$;

-- Grant execute to authenticated users and service_role
GRANT EXECUTE ON FUNCTION public.get_unscored_jobs_for_user TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_unscored_jobs_for_user TO service_role;
