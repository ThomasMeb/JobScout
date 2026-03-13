"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
    console.error("Global error:", error);
  }, [error]);

  return (
    <html lang="fr">
      <body className="flex min-h-screen items-center justify-center px-4" style={{ background: "#0C0C0E", color: "#F4F4F5" }}>
        <div className="text-center">
          <h1 className="text-2xl font-bold">
            <span style={{ color: "#FBBF24" }}>Job</span>
            <span>Scout</span>
          </h1>

          <p className="mt-6 text-lg font-semibold">Une erreur critique est survenue</p>
          <p className="mt-1 text-sm" style={{ color: "#A1A1AA" }}>
            Veuillez réessayer ou contacter le support.
          </p>

          <div className="mt-8 flex flex-col items-center gap-3">
            <button
              onClick={reset}
              className="rounded px-6 py-2.5 text-sm font-medium"
              style={{ background: "#F59E0B", color: "#0C0C0E" }}
            >
              Réessayer
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
