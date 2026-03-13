"use client";

import Link from "next/link";
import type { Job } from "@/lib/types";
import { updateJobFeedback } from "@/lib/api";
import { ScoreBadge, StatusBadge, RemoteBadge } from "@/components/Badges";
import { ExternalLinkIcon } from "@/components/Icons";

export default function JobCard({
  job,
  onRefresh,
  selected,
  onToggleSelect,
}: {
  job: Job;
  onRefresh: () => void;
  selected?: boolean;
  onToggleSelect?: (id: number) => void;
}) {
  async function handleFeedback(status: string) {
    try {
      await updateJobFeedback(job.id, status);
      onRefresh();
    } catch (e) {
      console.error("Feedback error:", e);
    }
  }

  const scoreColor = job.match_priority === "high" ? "border-l-positive" : job.match_priority === "medium" ? "border-l-amber" : "border-l-negative";

  return (
    <div
      className={`rounded border border-l-2 p-4 transition-colors ${
        selected
          ? `border-amber/30 ${scoreColor} bg-amber/5`
          : `border-border ${scoreColor} bg-surface-1`
      }`}
    >
      {/* Top row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {onToggleSelect && (
            <input
              type="checkbox"
              checked={selected || false}
              onChange={() => onToggleSelect(job.id)}
              className="h-4 w-4 rounded border-border accent-amber"
            />
          )}
          <ScoreBadge score={job.match_score} priority={job.match_priority} />
          <StatusBadge status={job.status} />
        </div>
        <span className="font-mono text-xs text-text-muted">{job.source}</span>
      </div>

      {/* Title */}
      <Link href={`/dashboard/${job.id}`} className="mt-2 block text-sm font-semibold text-amber hover:text-amber-bright transition-colors">
        {job.title}
      </Link>

      {/* Company + Location */}
      <p className="mt-1 text-sm text-text-secondary">{job.company}</p>
      <div className="mt-0.5 flex items-center gap-2 text-sm">
        <span className="text-text-muted">{job.location || "\u2014"}</span>
        <RemoteBadge type={job.remote_type} />
      </div>

      {/* Actions */}
      <div className="mt-3 flex gap-2">
        {job.status === "new" && (
          <>
            <button
              onClick={() => handleFeedback("interested")}
              className="flex-1 rounded bg-positive py-1.5 text-xs font-medium text-surface-0 hover:brightness-110 transition"
            >
              Intéressé
            </button>
            <button
              onClick={() => handleFeedback("rejected")}
              className="flex-1 rounded bg-surface-3 py-1.5 text-xs font-medium text-text-secondary hover:bg-border-hover transition-colors"
            >
              Refuser
            </button>
          </>
        )}
        {job.source_url && (
          <a
            href={job.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`flex items-center justify-center gap-1 rounded border border-amber/30 py-1.5 text-xs font-medium text-amber hover:bg-amber/10 transition-colors ${
              job.status === "new" ? "px-3" : "flex-1"
            }`}
          >
            <ExternalLinkIcon size={12} /> Voir
          </a>
        )}
      </div>
    </div>
  );
}
