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
      <body className="flex min-h-screen items-center justify-center bg-white px-4 text-gray-900 dark:bg-gray-900 dark:text-white">
        <div className="text-center">
          <h1 className="text-2xl font-bold">
            <span className="text-blue-600">Job</span>
            <span>Scout</span>
          </h1>

          <p className="mt-6 text-lg font-semibold">Something went wrong</p>
          <p className="mt-1 text-sm text-gray-500">
            A critical error occurred. Please try again.
          </p>

          <div className="mt-8 flex flex-col items-center gap-3">
            <button
              onClick={reset}
              className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
