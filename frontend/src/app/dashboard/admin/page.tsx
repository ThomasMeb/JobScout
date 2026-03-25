"use client";

import { useEffect, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import AppShell from "@/components/AppShell";
import { getAdminUsers, getAdminScrapers, getAdminMetrics } from "@/lib/api";

interface AdminUser {
  id: string;
  name: string | null;
  notification_email: string | null;
  plan: string;
  onboarding_completed: boolean;
  created_at: string;
  total_jobs: number;
}

interface ScraperInfo {
  source: string;
  total_runs: number;
  success_runs: number;
  success_rate: number;
  total_jobs_found: number;
  total_jobs_new: number;
  last_run: string | null;
  last_error: string | null;
}

interface Metrics {
  total_users: number;
  pro_users: number;
  total_raw_jobs: number;
  total_scored_jobs: number;
  worker_status: string;
  worker_cycles: number;
  worker_last_cycle: string | null;
}

function MetricCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded border border-border bg-surface-1 p-4">
      <p className="text-xs font-medium uppercase tracking-wider text-text-muted">{label}</p>
      <p className="mt-1 font-mono text-2xl font-bold text-text-primary">{typeof value === "number" ? value.toLocaleString() : value}</p>
    </div>
  );
}

export default function AdminPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [scrapers, setScrapers] = useState<ScraperInfo[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [usersRes, scrapersRes, metricsRes] = await Promise.all([
          getAdminUsers(),
          getAdminScrapers(),
          getAdminMetrics(),
        ]);
        setUsers(usersRes.users || []);
        setScrapers(scrapersRes.scrapers || []);
        setMetrics(metricsRes);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erreur lors du chargement des données admin");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <AuthGuard>
        <AppShell>
          <div className="flex min-h-[50vh] items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber border-t-transparent" />
          </div>
        </AppShell>
      </AuthGuard>
    );
  }

  if (error) {
    return (
      <AuthGuard>
        <AppShell>
          <div className="p-8 text-negative">{error}</div>
        </AppShell>
      </AuthGuard>
    );
  }

  const statusColor = (status: string) => {
    if (status === "running") return "text-positive";
    if (status === "error" || status === "crashed") return "text-negative";
    return "text-amber";
  };

  return (
    <AuthGuard>
      <AppShell>
        <div className="space-y-8 px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="font-display text-3xl italic text-text-primary" style={{ letterSpacing: "-0.02em" }}>Admin</h1>

          {/* Metrics */}
          {metrics && (
            <section>
              <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-text-muted">Métriques business</h2>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <MetricCard label="Utilisateurs" value={metrics.total_users} />
                <MetricCard label="Pro" value={metrics.pro_users} />
                <MetricCard label="Offres brutes" value={metrics.total_raw_jobs} />
                <MetricCard label="Offres évaluées" value={metrics.total_scored_jobs} />
              </div>
              <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
                <div className="rounded border border-border bg-surface-1 p-4">
                  <p className="text-xs font-medium uppercase tracking-wider text-text-muted">Worker</p>
                  <p className={`mt-1 font-mono text-xl font-bold ${statusColor(metrics.worker_status)}`}>
                    {metrics.worker_status}
                  </p>
                </div>
                <MetricCard label="Cycles" value={metrics.worker_cycles} />
                <div className="rounded border border-border bg-surface-1 p-4">
                  <p className="text-xs font-medium uppercase tracking-wider text-text-muted">Dernier cycle</p>
                  <p className="mt-1 font-mono text-sm text-text-primary">
                    {metrics.worker_last_cycle ? new Date(metrics.worker_last_cycle).toLocaleString() : "Jamais"}
                  </p>
                </div>
              </div>
            </section>
          )}

          {/* Scrapers */}
          <section>
            <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-text-muted">Santé des scrapers</h2>
            {scrapers.length === 0 ? (
              <p className="text-text-muted">Aucune donnée de scraper disponible.</p>
            ) : (
              <div className="overflow-x-auto rounded border border-border">
                <table className="w-full text-sm text-left">
                  <thead className="bg-surface-2 text-xs uppercase tracking-wider text-text-muted">
                    <tr>
                      {["Source", "Exéc.", "Succès", "Offres", "Nouvelles", "Dernier run", "Erreur"].map((h) => (
                        <th key={h} className="px-3 py-2.5">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {scrapers.map((s) => (
                      <tr key={s.source} className="text-text-secondary hover:bg-surface-2/50 transition-colors">
                        <td className="px-3 py-2.5 font-mono font-medium text-text-primary">{s.source}</td>
                        <td className="px-3 py-2.5 font-mono">{s.total_runs}</td>
                        <td className="px-3 py-2.5">
                          <div className="flex items-center gap-2">
                            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-3">
                              <div
                                className={`h-full rounded-full ${s.success_rate >= 80 ? "bg-positive" : s.success_rate >= 50 ? "bg-amber" : "bg-negative"}`}
                                style={{ width: `${s.success_rate}%` }}
                              />
                            </div>
                            <span className="font-mono text-xs">{s.success_rate}%</span>
                          </div>
                        </td>
                        <td className="px-3 py-2.5 font-mono">{s.total_jobs_found}</td>
                        <td className="px-3 py-2.5 font-mono">{s.total_jobs_new}</td>
                        <td className="px-3 py-2.5 font-mono text-xs">{s.last_run ? new Date(s.last_run).toLocaleString() : "—"}</td>
                        <td className="px-3 py-2.5 max-w-xs truncate text-xs text-negative">{s.last_error || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Users */}
          <section>
            <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-text-muted">
              Utilisateurs ({users.length})
            </h2>
            {users.length === 0 ? (
              <p className="text-text-muted">Aucun utilisateur trouvé.</p>
            ) : (
              <div className="overflow-x-auto rounded border border-border">
                <table className="w-full text-sm text-left">
                  <thead className="bg-surface-2 text-xs uppercase tracking-wider text-text-muted">
                    <tr>
                      {["Nom", "Email", "Plan", "Offres", "Config", "Inscription"].map((h) => (
                        <th key={h} className="px-3 py-2.5">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {users.map((u) => (
                      <tr key={u.id} className="text-text-secondary hover:bg-surface-2/50 transition-colors">
                        <td className="px-3 py-2.5 font-medium text-text-primary">{u.name || "—"}</td>
                        <td className="px-3 py-2.5 font-mono text-xs">{u.notification_email || "—"}</td>
                        <td className="px-3 py-2.5">
                          <span className={`rounded px-2 py-0.5 font-mono text-xs font-medium ${
                            u.plan === "pro" ? "bg-amber/10 text-amber" : "bg-surface-3 text-text-muted"
                          }`}>
                            {u.plan}
                          </span>
                        </td>
                        <td className="px-3 py-2.5 font-mono">{u.total_jobs}</td>
                        <td className="px-3 py-2.5">
                          <span className={`h-2 w-2 inline-block rounded-full ${u.onboarding_completed ? "bg-positive" : "bg-text-muted"}`} />
                        </td>
                        <td className="px-3 py-2.5 font-mono text-xs">{new Date(u.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
