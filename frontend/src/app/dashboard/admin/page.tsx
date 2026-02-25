"use client";

import { useEffect, useState } from "react";
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
        setError(err instanceof Error ? err.message : "Failed to load admin data");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div className="p-8 text-gray-400">Loading admin data...</div>;
  if (error) return <div className="p-8 text-red-400">{error}</div>;

  const statusColor = (status: string) => {
    if (status === "running") return "text-green-400";
    if (status === "error" || status === "crashed") return "text-red-400";
    return "text-yellow-400";
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>

      {/* Business Metrics */}
      {metrics && (
        <section>
          <h2 className="text-lg font-semibold text-gray-200 mb-4">Business Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard label="Total Users" value={metrics.total_users} />
            <MetricCard label="Pro Users" value={metrics.pro_users} />
            <MetricCard label="Raw Jobs" value={metrics.total_raw_jobs} />
            <MetricCard label="Scored Jobs" value={metrics.total_scored_jobs} />
          </div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-lg p-4">
              <p className="text-sm text-gray-400">Worker Status</p>
              <p className={`text-xl font-bold ${statusColor(metrics.worker_status)}`}>
                {metrics.worker_status}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <p className="text-sm text-gray-400">Worker Cycles</p>
              <p className="text-xl font-bold text-white">{metrics.worker_cycles}</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <p className="text-sm text-gray-400">Last Cycle</p>
              <p className="text-sm text-white">
                {metrics.worker_last_cycle
                  ? new Date(metrics.worker_last_cycle).toLocaleString()
                  : "Never"}
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Scraper Health */}
      <section>
        <h2 className="text-lg font-semibold text-gray-200 mb-4">Scraper Health</h2>
        {scrapers.length === 0 ? (
          <p className="text-gray-400">No scraper data available.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-gray-400 border-b border-gray-700">
                <tr>
                  <th className="py-2 px-3">Source</th>
                  <th className="py-2 px-3">Runs</th>
                  <th className="py-2 px-3">Success Rate</th>
                  <th className="py-2 px-3">Jobs Found</th>
                  <th className="py-2 px-3">New Jobs</th>
                  <th className="py-2 px-3">Last Run</th>
                  <th className="py-2 px-3">Last Error</th>
                </tr>
              </thead>
              <tbody>
                {scrapers.map((s) => (
                  <tr key={s.source} className="border-b border-gray-800 text-gray-300">
                    <td className="py-2 px-3 font-medium text-white">{s.source}</td>
                    <td className="py-2 px-3">{s.total_runs}</td>
                    <td className="py-2 px-3">
                      <span
                        className={
                          s.success_rate >= 80
                            ? "text-green-400"
                            : s.success_rate >= 50
                              ? "text-yellow-400"
                              : "text-red-400"
                        }
                      >
                        {s.success_rate}%
                      </span>
                    </td>
                    <td className="py-2 px-3">{s.total_jobs_found}</td>
                    <td className="py-2 px-3">{s.total_jobs_new}</td>
                    <td className="py-2 px-3 text-xs">
                      {s.last_run ? new Date(s.last_run).toLocaleString() : "—"}
                    </td>
                    <td className="py-2 px-3 text-xs text-red-400 max-w-xs truncate">
                      {s.last_error || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Users */}
      <section>
        <h2 className="text-lg font-semibold text-gray-200 mb-4">
          Users ({users.length})
        </h2>
        {users.length === 0 ? (
          <p className="text-gray-400">No users found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-gray-400 border-b border-gray-700">
                <tr>
                  <th className="py-2 px-3">Name</th>
                  <th className="py-2 px-3">Email</th>
                  <th className="py-2 px-3">Plan</th>
                  <th className="py-2 px-3">Jobs</th>
                  <th className="py-2 px-3">Onboarded</th>
                  <th className="py-2 px-3">Joined</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-gray-800 text-gray-300">
                    <td className="py-2 px-3 font-medium text-white">
                      {u.name || "—"}
                    </td>
                    <td className="py-2 px-3 text-xs">{u.notification_email || "—"}</td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          u.plan === "pro"
                            ? "bg-blue-900 text-blue-300"
                            : "bg-gray-700 text-gray-300"
                        }`}
                      >
                        {u.plan}
                      </span>
                    </td>
                    <td className="py-2 px-3">{u.total_jobs}</td>
                    <td className="py-2 px-3">
                      {u.onboarding_completed ? "Yes" : "No"}
                    </td>
                    <td className="py-2 px-3 text-xs">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <p className="text-sm text-gray-400">{label}</p>
      <p className="text-2xl font-bold text-white">{value.toLocaleString()}</p>
    </div>
  );
}
