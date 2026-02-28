"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Charts from "@/components/Charts";
import FilterBar from "@/components/FilterBar";
import JobCard from "@/components/JobCard";
import JobTable from "@/components/JobTable";
import MobileNav from "@/components/MobileNav";
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
        <MobileNav />

        <div className="mx-auto max-w-7xl space-y-4 px-4 py-4 sm:space-y-6 sm:px-6 sm:py-6">
          {stats && <StatsBar stats={stats} />}
          <Charts />
          <WorkerStatus />

          {/* Search */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Rechercher des offres..."
              className="flex-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800"
            />
            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              Rechercher
            </button>
            {searchQuery && (
              <button
                type="button"
                onClick={() => { setSearchInput(""); setSearchQuery(""); setPage(1); }}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800"
              >
                Effacer
              </button>
            )}
          </form>

          {/* Filters */}
          <FilterBar
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            minScore={minScore}
            setMinScore={setMinScore}
            sourceFilter={sourceFilter}
            setSourceFilter={setSourceFilter}
            total={total}
            onPageReset={() => setPage(1)}
          />

          {/* Bulk actions + Export */}
          <div className="flex flex-wrap items-center gap-2">
            {selected.size > 0 && (
              <div className="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 dark:border-blue-800 dark:bg-blue-950">
                <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                  {selected.size} sélectionné{selected.size > 1 ? "s" : ""}
                </span>
                <button
                  onClick={() => handleBulkAction("interested")}
                  className="rounded bg-green-600 px-2 py-0.5 text-xs font-medium text-white hover:bg-green-700"
                >
                  Intéressé
                </button>
                <button
                  onClick={() => handleBulkAction("rejected")}
                  className="rounded bg-red-600 px-2 py-0.5 text-xs font-medium text-white hover:bg-red-700"
                >
                  Refuser
                </button>
                <button
                  onClick={() => handleBulkAction("new")}
                  className="rounded bg-gray-500 px-2 py-0.5 text-xs font-medium text-white hover:bg-gray-600"
                >
                  Réinitialiser
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
              Exporter CSV
            </button>
          </div>

          {/* Job listings */}
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
            </div>
          ) : (
            <>
              {/* Desktop: table */}
              <div className="hidden md:block">
                <JobTable
                  jobs={jobs}
                  onRefresh={fetchData}
                  selected={selected}
                  onToggleSelect={toggleSelect}
                  onToggleSelectAll={toggleSelectAll}
                />
              </div>

              {/* Mobile: cards */}
              <div className="space-y-3 md:hidden">
                {jobs.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center dark:border-gray-600">
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Aucune offre trouvée.
                    </p>
                  </div>
                ) : (
                  jobs.map((job) => (
                    <JobCard
                      key={job.id}
                      job={job}
                      onRefresh={fetchData}
                      selected={selected.has(job.id)}
                      onToggleSelect={toggleSelect}
                    />
                  ))
                )}
              </div>
            </>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm disabled:opacity-50 dark:border-gray-600"
              >
                Précédent
              </button>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page >= totalPages}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm disabled:opacity-50 dark:border-gray-600"
              >
                Suivant
              </button>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
