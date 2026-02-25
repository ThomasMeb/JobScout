"use client";

import Link from "next/link";
import type { Job } from "@/lib/types";
import { updateJobFeedback } from "@/lib/api";
import { ScoreBadge, StatusBadge, RemoteBadge } from "@/components/Badges";

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

  return (
    <div
      className={`rounded-lg border p-4 ${
        selected
          ? "border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-950"
          : "border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900"
      }`}
    >
      {/* Top row: checkbox + score + status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {onToggleSelect && (
            <input
              type="checkbox"
              checked={selected || false}
              onChange={() => onToggleSelect(job.id)}
              className="h-4 w-4 rounded border-gray-300"
            />
          )}
          <ScoreBadge score={job.match_score} priority={job.match_priority} />
          <StatusBadge status={job.status} />
        </div>
        <span className="text-xs text-gray-400">{job.source}</span>
      </div>

      {/* Title */}
      <Link
        href={`/dashboard/${job.id}`}
        className="mt-2 block text-sm font-semibold text-blue-600 hover:underline dark:text-blue-400"
      >
        {job.title}
      </Link>

      {/* Company + Location */}
      <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">{job.company}</p>
      <div className="mt-0.5 flex items-center gap-2 text-sm">
        <span className="text-gray-500 dark:text-gray-400">{job.location || "\u2014"}</span>
        <RemoteBadge type={job.remote_type} />
      </div>

      {/* Actions */}
      <div className="mt-3 flex gap-2">
        {job.status === "new" && (
          <>
            <button
              onClick={() => handleFeedback("interested")}
              className="flex-1 rounded-lg bg-green-600 py-1.5 text-xs font-medium text-white hover:bg-green-700"
            >
              Interested
            </button>
            <button
              onClick={() => handleFeedback("rejected")}
              className="flex-1 rounded-lg bg-gray-200 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
            >
              Reject
            </button>
          </>
        )}
        {job.source_url && (
          <a
            href={job.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`rounded-lg border border-blue-200 py-1.5 text-center text-xs font-medium text-blue-700 hover:bg-blue-50 dark:border-blue-800 dark:text-blue-300 dark:hover:bg-blue-950 ${
              job.status === "new" ? "" : "flex-1"
            }`}
            style={job.status !== "new" ? {} : { padding: "0 12px" }}
          >
            View
          </a>
        )}
      </div>
    </div>
  );
}
