"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import AppShell from "@/components/AppShell";
import Charts from "@/components/Charts";
import FilterBar from "@/components/FilterBar";
import JobCard from "@/components/JobCard";
import JobTable from "@/components/JobTable";
import StatsBar from "@/components/StatsBar";
import WorkerStatus from "@/components/WorkerStatus";
import { SearchIcon, DownloadIcon } from "@/components/Icons";
import { toast } from "sonner";
import { bulkFeedback, exportJobsCSV, getJobs, getProfile, getStats } from "@/lib/api";
import type { Job, JobListResponse, Profile, UserStats } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [minScore, setMinScore] = useState<number | "">("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
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
      toast.error("Erreur lors du chargement du tableau de bord");
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
    try {
      await bulkFeedback(Array.from(selected), status);
      toast.success(`${selected.size} offre(s) mise(s) à jour`);
      await fetchData();
    } catch {
      toast.error("Erreur lors de la mise à jour");
    }
  }

  const totalPages = Math.ceil(total / perPage);

  return (
    <AuthGuard>
      <AppShell>
        <div className="space-y-4 px-4 py-6 sm:space-y-6 sm:px-6 lg:px-8">
          {/* Welcome header */}
          <div>
            <h1 className="font-display text-3xl italic text-text-primary" style={{ letterSpacing: "-0.02em" }}>
              Tableau de bord
            </h1>
            <p className="mt-1 text-sm text-text-secondary">
              Vos offres d&apos;emploi, analysées par IA.
            </p>
            <div className="editorial-divider mt-3 w-12" />
          </div>

          {stats && <StatsBar stats={stats} />}
          <Charts />
          <WorkerStatus />

          {/* Search */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <SearchIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Rechercher des offres..."
                className="w-full rounded border border-border bg-surface-1 py-2 pl-9 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:border-amber focus:outline-none focus:ring-1 focus:ring-amber transition-colors"
              />
            </div>
            <button
              type="submit"
              className="rounded bg-amber px-4 py-2 text-sm font-medium text-surface-0 hover:bg-amber-bright transition-colors"
            >
              Rechercher
            </button>
            {searchQuery && (
              <button
                type="button"
                onClick={() => { setSearchInput(""); setSearchQuery(""); setPage(1); }}
                className="rounded border border-border px-3 py-2 text-sm text-text-secondary hover:border-border-hover hover:text-text-primary transition-colors"
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
              <div className="flex items-center gap-2 rounded border border-amber/30 bg-amber/5 px-3 py-1.5">
                <span className="text-sm font-medium text-amber">
                  {selected.size} sélectionné{selected.size > 1 ? "s" : ""}
                </span>
                <button onClick={() => handleBulkAction("interested")} className="rounded bg-positive px-2 py-0.5 text-xs font-medium text-surface-0 hover:brightness-110">
                  Intéressé
                </button>
                <button onClick={() => handleBulkAction("rejected")} className="rounded bg-negative px-2 py-0.5 text-xs font-medium text-surface-0 hover:brightness-110">
                  Refuser
                </button>
                <button onClick={() => handleBulkAction("new")} className="rounded bg-surface-3 px-2 py-0.5 text-xs font-medium text-text-secondary hover:brightness-110">
                  Réinitialiser
                </button>
              </div>
            )}
            <button
              onClick={() => exportJobsCSV({ min_score: minScore || undefined, status: statusFilter || undefined }).then(() => toast.success("Export CSV téléchargé")).catch(() => toast.error("Erreur lors de l'export"))}
              className="ml-auto flex items-center gap-2 rounded border border-border px-3 py-1.5 text-sm text-text-secondary hover:border-border-hover hover:text-text-primary transition-colors"
            >
              <DownloadIcon size={14} />
              Exporter CSV
            </button>
          </div>

          {/* Job listings */}
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber border-t-transparent" />
            </div>
          ) : (
            <>
              <div className="hidden md:block">
                <JobTable jobs={jobs} onRefresh={fetchData} selected={selected} onToggleSelect={toggleSelect} onToggleSelectAll={toggleSelectAll} />
              </div>
              <div className="space-y-3 md:hidden">
                {jobs.length === 0 ? (
                  <div className="rounded border border-dashed border-border p-8 text-center">
                    <p className="text-sm text-text-muted">Aucune offre trouvée.</p>
                  </div>
                ) : (
                  jobs.map((job) => (
                    <JobCard key={job.id} job={job} onRefresh={fetchData} selected={selected.has(job.id)} onToggleSelect={toggleSelect} />
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
                className="rounded border border-border px-3 py-1.5 text-sm text-text-secondary disabled:opacity-50 hover:border-border-hover transition-colors"
              >
                Précédent
              </button>
              <span className="font-mono text-sm text-text-muted">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page >= totalPages}
                className="rounded border border-border px-3 py-1.5 text-sm text-text-secondary disabled:opacity-50 hover:border-border-hover transition-colors"
              >
                Suivant
              </button>
            </div>
          )}
        </div>
      </AppShell>
    </AuthGuard>
  );
}
