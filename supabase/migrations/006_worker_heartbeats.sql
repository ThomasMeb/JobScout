-- Worker heartbeat tracking for uptime monitoring
CREATE TABLE IF NOT EXISTS public.worker_heartbeats (
    id TEXT PRIMARY KEY DEFAULT 'main',
    last_cycle_at TIMESTAMPTZ,
    cycle_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'starting',
    error_message TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.worker_heartbeats ENABLE ROW LEVEL SECURITY;

-- Only service role can read/write heartbeats
CREATE POLICY "service_role_only" ON public.worker_heartbeats
    FOR ALL USING (auth.role() = 'service_role');
