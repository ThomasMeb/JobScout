"use client";

import Link from "next/link";
import type { Job } from "@/lib/types";
import { updateJobFeedback } from "@/lib/api";

function ScoreBadge({ score, priority }: { score: number | null; priority: string }) {
  if (score === null) return <span className="text-gray-400">—</span>;

  const colors: Record<string, string> = {
    high: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    low: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  };

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[priority] || colors.low}`}>
      {Math.round(score)}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    new: "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
    interested: "bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300",
    applied: "bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
    rejected: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
  };

  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors[status] || colors.new}`}>
      {status}
    </span>
  );
}

function RemoteBadge({ type }: { type: string }) {
  if (type === "full") return <span className="text-xs text-green-600">Remote</span>;
  if (type === "partial") return <span className="text-xs text-blue-600">Hybrid</span>;
  return <span className="text-xs text-gray-500">On-site</span>;
}

export default function JobTable({
  jobs,
  onRefresh,
}: {
  jobs: Job[];
  onRefresh: () => void;
}) {
  async function handleFeedback(jobId: number, status: string) {
    try {
      await updateJobFeedback(jobId, status);
      onRefresh();
    } catch (e) {
      console.error("Feedback error:", e);
    }
  }

  if (!jobs.length) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 p-12 text-center dark:border-gray-600">
        <p className="text-gray-500 dark:text-gray-400">
          No jobs found. Jobs will appear after the worker runs its first cycle.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
          {jobs.map((job) => (
            <tr key={job.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
              <td className="px-4 py-3">
                <ScoreBadge score={job.match_score} priority={job.match_priority} />
              </td>
              <td className="px-4 py-3">
                <Link
                  href={`/dashboard/${job.id}`}
                  className="font-medium text-blue-600 hover:underline dark:text-blue-400"
                >
                  {job.title}
                </Link>
              </td>
              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                {job.company}
              </td>
              <td className="px-4 py-3 text-sm">
                <span className="text-gray-600 dark:text-gray-400">{job.location || "—"}</span>
                <RemoteBadge type={job.remote_type} />
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">{job.source}</td>
              <td className="px-4 py-3">
                <StatusBadge status={job.status} />
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-1">
                  {job.status === "new" && (
                    <>
                      <button
                        onClick={() => handleFeedback(job.id, "interested")}
                        className="rounded bg-green-100 px-2 py-1 text-xs text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300"
                      >
                        Interested
                      </button>
                      <button
                        onClick={() => handleFeedback(job.id, "rejected")}
                        className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400"
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
                      className="rounded bg-blue-100 px-2 py-1 text-xs text-blue-700 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-300"
                    >
                      View
                    </a>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
