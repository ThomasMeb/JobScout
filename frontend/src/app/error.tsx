"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("Route error:", error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-0 px-4">
      <div className="text-center">
        <p className="font-mono text-5xl font-bold text-negative">Erreur</p>
        <p className="mt-4 text-lg font-semibold text-text-primary">Une erreur est survenue</p>
        <p className="mt-1 text-sm text-text-muted">
          Une erreur inattendue s&apos;est produite. Veuillez réessayer.
        </p>

        <div className="mt-8 flex flex-col items-center gap-3">
          <button onClick={reset} className="rounded bg-amber px-6 py-2.5 text-sm font-medium text-surface-0 hover:bg-amber-bright transition-colors">
            Réessayer
          </button>
          <Link href="/dashboard" className="text-sm text-text-muted hover:text-text-primary transition-colors">
            Retour au tableau de bord
          </Link>
        </div>
      </div>
    </div>
  );
}
