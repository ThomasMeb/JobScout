"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase-browser";
import { isMockMode } from "@/lib/mock-data";
import type { Session } from "@supabase/supabase-js";

const MOCK_SESSION = { access_token: "mock-token", user: { id: "mock-user-001", email: "thomas@mebarki.dev" } } as unknown as Session;
const WARN_BEFORE_MS = 2 * 60 * 1000; // warn 2 min before expiry

async function isApiReachable(): Promise<boolean> {
  const url = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${url}/api/health`, { signal: AbortSignal.timeout(2000) });
    return res.ok;
  } catch {
    return false;
  }
}

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const warnTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  function scheduleExpiryWarning(sess: Session) {
    if (warnTimerRef.current) clearTimeout(warnTimerRef.current);
    const exp = sess.expires_at;
    if (!exp) return;
    const msUntilWarn = exp * 1000 - Date.now() - WARN_BEFORE_MS;
    if (msUntilWarn <= 0) return;
    warnTimerRef.current = setTimeout(() => {
      toast.warning("Votre session expire bientôt — sauvegardez votre travail", { duration: 10000 });
    }, msUntilWarn);
  }

  useEffect(() => {
    if (isMockMode()) {
      setSession(MOCK_SESSION);
      setLoading(false);
      return;
    }

    const supabase = createClient();

    supabase.auth.getSession().then(async ({ data }: { data: { session: Session | null } }) => {
      if (data.session) {
        setSession(data.session);
        scheduleExpiryWarning(data.session);
        setLoading(false);
      } else {
        const reachable = await isApiReachable();
        if (!reachable) {
          setSession(MOCK_SESSION);
        } else {
          router.replace("/login");
        }
        setLoading(false);
      }
    }).catch(() => {
      setSession(MOCK_SESSION);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(
      (_event: string, newSession: Session | null) => {
        if (!newSession) {
          router.replace("/login");
        } else {
          setSession(newSession);
          scheduleExpiryWarning(newSession);
        }
      }
    );

    return () => {
      subscription.unsubscribe();
      if (warnTimerRef.current) clearTimeout(warnTimerRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-surface-0">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber border-t-transparent" />
      </div>
    );
  }

  if (!session) return null;

  return <>{children}</>;
}
