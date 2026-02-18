"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import { getJob, updateJobFeedback } from "@/lib/api";
import type { Job } from "@/lib/types";

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    getJob(Number(id))
      .then((j) => {
        setJob(j);
        setNotes(j.user_notes || "");
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  async function handleFeedback(status: string) {
    if (!job) return;
    try {
      const updated = await updateJobFeedback(job.id, status, notes || undefined);
      setJob(updated);
    } catch (e) {
      console.error(e);
    }
  }

  if (loading) {
    return (
      <AuthGuard>
        <div className="flex min-h-screen items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
        </div>
      </AuthGuard>
    );
  }

  if (!job) {
    return (
      <AuthGuard>
        <div className="flex min-h-screen items-center justify-center">
          <p className="text-gray-500">Job not found</p>
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <nav className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
          <div className="mx-auto flex max-w-4xl items-center gap-4 px-6 py-3">
            <button
              onClick={() => router.back()}
              className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400"
            >
              &larr; Back
            </button>
            <h1 className="text-lg font-bold">
              <span className="text-blue-600">Job</span>Scout
            </h1>
          </div>
        </nav>

        <div className="mx-auto max-w-4xl space-y-6 px-6 py-6">
          {/* Header */}
          <div>
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold">{job.title}</h2>
                <p className="text-lg text-gray-600 dark:text-gray-400">
                  {job.company} &middot; {job.location || "Location N/A"}
                </p>
              </div>
              {job.match_score !== null && (
                <div className="text-right">
                  <div className="text-3xl font-bold text-blue-600">
                    {Math.round(job.match_score)}
                  </div>
                  <div className="text-sm text-gray-500">/ 100</div>
                </div>
              )}
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <span className="rounded-full bg-gray-100 px-3 py-1 text-sm dark:bg-gray-800">
                {job.source}
              </span>
              <span className="rounded-full bg-gray-100 px-3 py-1 text-sm dark:bg-gray-800">
                {job.remote_type === "full" ? "Remote" : job.remote_type === "partial" ? "Hybrid" : "On-site"}
              </span>
              {job.salary_min && (
                <span className="rounded-full bg-gray-100 px-3 py-1 text-sm dark:bg-gray-800">
                  {job.salary_min}
                  {job.salary_max ? `-${job.salary_max}` : "+"} {job.salary_currency}
                </span>
              )}
              <span className={`rounded-full px-3 py-1 text-sm font-medium ${
                job.status === "interested" ? "bg-green-100 text-green-700" :
                job.status === "applied" ? "bg-purple-100 text-purple-700" :
                job.status === "rejected" ? "bg-gray-200 text-gray-600" :
                "bg-blue-100 text-blue-700"
              }`}>
                {job.status}
              </span>
            </div>
          </div>

          {/* Scoring breakdown */}
          {job.match_reasoning && (
            <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
              <h3 className="mb-2 font-semibold">AI Scoring breakdown</h3>
              <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300">
                {job.match_reasoning}
              </pre>
              {job.match_keywords.length > 0 && (
                <div className="mt-3">
                  <span className="text-sm font-medium text-green-600">Match: </span>
                  <span className="text-sm">{job.match_keywords.join(", ")}</span>
                </div>
              )}
              {job.missing_keywords.length > 0 && (
                <div className="mt-1">
                  <span className="text-sm font-medium text-red-600">Missing: </span>
                  <span className="text-sm">{job.missing_keywords.join(", ")}</span>
                </div>
              )}
            </div>
          )}

          {/* Notes + Actions */}
          <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-2 font-semibold">Notes</h3>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
              placeholder="Add personal notes about this job..."
            />

            <div className="mt-4 flex flex-wrap gap-2">
              <button
                onClick={() => handleFeedback("interested")}
                className="rounded-lg bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700"
              >
                Interested
              </button>
              <button
                onClick={() => handleFeedback("applied")}
                className="rounded-lg bg-purple-600 px-4 py-2 text-sm text-white hover:bg-purple-700"
              >
                Applied
              </button>
              <button
                onClick={() => handleFeedback("rejected")}
                className="rounded-lg bg-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-400 dark:bg-gray-600 dark:text-gray-200"
              >
                Reject
              </button>
              {job.source_url && (
                <a
                  href={job.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
                >
                  View original
                </a>
              )}
              {job.apply_url && (
                <a
                  href={job.apply_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-lg border border-blue-600 px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                >
                  Apply
                </a>
              )}
            </div>
          </div>

          {/* Tags */}
          {job.tags.length > 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
              <h3 className="mb-2 font-semibold">Tags</h3>
              <div className="flex flex-wrap gap-1">
                {job.tags.map((tag, i) => (
                  <span key={i} className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs dark:bg-gray-700">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
