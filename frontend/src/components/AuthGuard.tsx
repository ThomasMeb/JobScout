"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";
import { isMockMode } from "@/lib/mock-data";
import type { Session } from "@supabase/supabase-js";

const MOCK_SESSION = { access_token: "mock-token", user: { id: "mock-user-001", email: "thomas@mebarki.dev" } } as unknown as Session;

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
        setLoading(false);
      } else {
        // No session — check if backend is also down (= local dev without backend)
        const reachable = await isApiReachable();
        if (!reachable) {
          // Backend down → use mock data
          setSession(MOCK_SESSION);
        } else {
          // Backend is up but no session → real login needed
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
        }
      }
    );

    return () => subscription.unsubscribe();
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
