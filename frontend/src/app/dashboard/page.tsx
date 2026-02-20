"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import JobTable from "@/components/JobTable";
import StatsBar from "@/components/StatsBar";
import WorkerStatus from "@/components/WorkerStatus";
import { getJobs, getProfile, getStats } from "@/lib/api";
import type { Job, JobListResponse, Profile, UserStats } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [minScore, setMinScore] = useState<number | "">("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");

  const perPage = 20;

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const profile: Profile = await getProfile();
      if (!profile.onboarding_completed) {
        router.replace("/onboarding");
        return;
      }

      const [jobsRes, statsRes]: [JobListResponse, UserStats] = await Promise.all([
        getJobs({
          page,
          per_page: perPage,
          min_score: minScore || undefined,
          status: statusFilter || undefined,
          source: sourceFilter || undefined,
        }),
        getStats(),
      ]);

      setJobs(jobsRes.jobs);
      setTotal(jobsRes.total);
      setStats(statsRes);
    } catch (e) {
      console.error("Failed to load dashboard:", e);
    } finally {
      setLoading(false);
    }
  }, [page, minScore, statusFilter, sourceFilter, router]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const totalPages = Math.ceil(total / perPage);

  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        {/* Nav */}
        <nav className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
            <h1 className="text-lg font-bold">
              <span className="text-blue-600">Job</span>Scout
            </h1>
            <a
              href="/settings"
              className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
            >
              Settings
            </a>
          </div>
        </nav>

        <div className="mx-auto max-w-7xl space-y-6 px-6 py-6">
          {stats && <StatsBar stats={stats} />}
          <WorkerStatus />

          {/* Filters */}
          <div className="flex flex-wrap gap-3">
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800"
            >
              <option value="">All statuses</option>
              <option value="new">New</option>
              <option value="interested">Interested</option>
              <option value="applied">Applied</option>
              <option value="rejected">Rejected</option>
            </select>

            <select
              value={minScore === "" ? "" : String(minScore)}
              onChange={(e) => { setMinScore(e.target.value ? Number(e.target.value) : ""); setPage(1); }}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800"
            >
              <option value="">Any score</option>
              <option value="70">70+</option>
              <option value="50">50+</option>
              <option value="30">30+</option>
            </select>

            <select
              value={sourceFilter}
              onChange={(e) => { setSourceFilter(e.target.value); setPage(1); }}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800"
            >
              <option value="">All sources</option>
              <option value="wttj">WTTJ</option>
              <option value="remoteok">RemoteOK</option>
              <option value="adzuna">Adzuna</option>
              <option value="francetravail">France Travail</option>
              <option value="jobspy">JobSpy</option>
            </select>

            <span className="self-center text-sm text-gray-500">
              {total} job{total !== 1 ? "s" : ""}
            </span>
          </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
            </div>
          ) : (
            <JobTable jobs={jobs} onRefresh={fetchData} />
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm disabled:opacity-50 dark:border-gray-600"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page >= totalPages}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm disabled:opacity-50 dark:border-gray-600"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
