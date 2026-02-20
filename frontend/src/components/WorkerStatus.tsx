"use client";

import { useEffect, useState } from "react";
import { getScrapeRuns } from "@/lib/api";
import type { ScrapeRun } from "@/lib/types";

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function WorkerStatus() {
  const [runs, setRuns] = useState<ScrapeRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getScrapeRuns(10)
      .then(setRuns)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading || runs.length === 0) return null;

  const lastRun = runs[0];
  const lastFinished = lastRun.finished_at || lastRun.started_at;
  const totalNew = runs.reduce((sum, r) => sum + r.jobs_new, 0);
  const hasError = runs.some((r) => r.status === "error");

  return (
    <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm dark:border-gray-700 dark:bg-gray-900">
      <span
        className={`inline-block h-2 w-2 rounded-full ${
          lastRun.status === "running"
            ? "animate-pulse bg-yellow-400"
            : hasError
              ? "bg-red-400"
              : "bg-green-400"
        }`}
      />
      <span className="text-gray-600 dark:text-gray-400">
        Last scan: {lastFinished ? timeAgo(lastFinished) : "unknown"}
      </span>
      <span className="text-gray-400 dark:text-gray-600">|</span>
      <span className="text-gray-600 dark:text-gray-400">
        {totalNew} new job{totalNew !== 1 ? "s" : ""} found
      </span>
      {hasError && (
        <>
          <span className="text-gray-400 dark:text-gray-600">|</span>
          <span className="text-red-500">Some scrapers had errors</span>
        </>
      )}
    </div>
  );
}
