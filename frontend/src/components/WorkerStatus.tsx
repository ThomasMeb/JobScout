"use client";

import { useEffect, useState } from "react";
import { getScrapeRuns } from "@/lib/api";
import type { ScrapeRun } from "@/lib/types";

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "à l'instant";
  if (mins < 60) return `il y a ${mins} min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `il y a ${hours}h`;
  return `il y a ${Math.floor(hours / 24)}j`;
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
  const isRunning = lastRun.status === "running";

  return (
    <div className="flex items-center gap-3 rounded border border-border bg-surface-1 px-4 py-2.5 text-sm">
      <span
        className={`inline-block h-2 w-2 rounded-full ${
          isRunning
            ? "animate-pulse bg-amber"
            : hasError
              ? "bg-negative"
              : "bg-positive"
        }`}
      />
      <span className="text-text-secondary">
        Dernier scan : <span className="font-mono text-text-primary">{lastFinished ? timeAgo(lastFinished) : "inconnu"}</span>
      </span>
      <span className="text-border-hover">|</span>
      <span className="text-text-secondary">
        <span className="font-mono text-text-primary">{totalNew}</span> nouvelle{totalNew !== 1 ? "s" : ""} offre{totalNew !== 1 ? "s" : ""}
      </span>
      {hasError && (
        <>
          <span className="text-border-hover">|</span>
          <span className="text-negative">Erreurs détectées</span>
        </>
      )}
    </div>
  );
}
