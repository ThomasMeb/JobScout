"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";
import { isMockMode } from "@/lib/mock-data";
import type { Session } from "@supabase/supabase-js";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Mock mode: skip auth entirely
    if (isMockMode()) {
      setSession({ access_token: "mock-token", user: { id: "mock-user-001", email: "thomas@mebarki.dev" } } as unknown as Session);
      setLoading(false);
      return;
    }

    const supabase = createClient();

    supabase.auth.getSession().then(({ data }: { data: { session: Session | null } }) => {
      if (!data.session) {
        router.replace("/login");
      } else {
        setSession(data.session);
      }
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
