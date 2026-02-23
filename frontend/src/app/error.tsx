"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Route error:", error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-2xl font-bold">
          <span className="text-blue-600">Job</span>
          <span className="text-gray-900 dark:text-white">Scout</span>
        </h1>

        <p className="mt-6 text-lg font-semibold text-gray-900 dark:text-white">
          Something went wrong
        </p>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-500">
          An unexpected error occurred. Please try again.
        </p>

        <div className="mt-8 flex flex-col items-center gap-3">
          <button
            onClick={reset}
            className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            Try again
          </button>
          <Link
            href="/dashboard"
            className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          >
            Back to dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
