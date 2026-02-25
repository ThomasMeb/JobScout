"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Charts from "@/components/Charts";
import JobTable from "@/components/JobTable";
import StatsBar from "@/components/StatsBar";
import WorkerStatus from "@/components/WorkerStatus";
import { bulkFeedback, exportJobsCSV, getJobs, getProfile, getStats } from "@/lib/api";
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
  const [searchQuery, setSearchQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");

  // Bulk selection
  const [selected, setSelected] = useState<Set<number>>(new Set());

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
          search: searchQuery || undefined,
        }),
        getStats(),
      ]);

      setJobs(jobsRes.jobs);
      setTotal(jobsRes.total);
      setStats(statsRes);
      setSelected(new Set());
    } catch (e) {
      console.error("Failed to load dashboard:", e);
    } finally {
      setLoading(false);
    }
  }, [page, minScore, statusFilter, sourceFilter, searchQuery, router]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setSearchQuery(searchInput);
    setPage(1);
  }

  function toggleSelect(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleSelectAll() {
    if (selected.size === jobs.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(jobs.map((j) => j.id)));
    }
  }

  async function handleBulkAction(status: string) {
    if (selected.size === 0) return;
    await bulkFeedback(Array.from(selected), status);
    await fetchData();
  }

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
            <div className="flex items-center gap-4">
              <a
                href="/dashboard/billing"
                className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
              >
                Billing
              </a>
              <a
                href="/settings"
                className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
              >
                Settings
              </a>
            </div>
          </div>
        </nav>

        <div className="mx-auto max-w-7xl space-y-6 px-6 py-6">
          {stats && <StatsBar stats={stats} />}
          <Charts />
          <WorkerStatus />

          {/* Search */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search jobs by title or company..."
              className="flex-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800"
            />
            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              Search
            </button>
            {searchQuery && (
              <button
                type="button"
                onClick={() => { setSearchInput(""); setSearchQuery(""); setPage(1); }}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800"
              >
                Clear
              </button>
            )}
          </form>

          {/* Filters + Bulk actions */}
          <div className="flex flex-wrap items-center gap-3">
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

            <span className="text-sm text-gray-500">
              {total} job{total !== 1 ? "s" : ""}
            </span>

            {/* Bulk actions */}
            {selected.size > 0 && (
              <div className="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 dark:border-blue-800 dark:bg-blue-950">
                <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                  {selected.size} selected
                </span>
                <button
                  onClick={() => handleBulkAction("interested")}
                  className="rounded bg-green-600 px-2 py-0.5 text-xs font-medium text-white hover:bg-green-700"
                >
                  Interested
                </button>
                <button
                  onClick={() => handleBulkAction("rejected")}
                  className="rounded bg-red-600 px-2 py-0.5 text-xs font-medium text-white hover:bg-red-700"
                >
                  Reject
                </button>
                <button
                  onClick={() => handleBulkAction("new")}
                  className="rounded bg-gray-500 px-2 py-0.5 text-xs font-medium text-white hover:bg-gray-600"
                >
                  Reset
                </button>
              </div>
            )}

            <button
              onClick={() => exportJobsCSV({
                min_score: minScore || undefined,
                status: statusFilter || undefined,
              })}
              className="ml-auto rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              Export CSV
            </button>
          </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
            </div>
          ) : (
            <JobTable
              jobs={jobs}
              onRefresh={fetchData}
              selected={selected}
              onToggleSelect={toggleSelect}
              onToggleSelectAll={toggleSelectAll}
            />
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
