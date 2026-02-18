"use client";

import type { UserStats } from "@/lib/types";

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
      <p className={`text-2xl font-bold ${color || "text-gray-900 dark:text-white"}`}>
        {value}
      </p>
    </div>
  );
}

export default function StatsBar({ stats }: { stats: UserStats }) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
      <StatCard label="Total jobs" value={stats.total_jobs} />
      <StatCard label="New" value={stats.new_jobs} color="text-blue-600" />
      <StatCard label="Interested" value={stats.interested} color="text-green-600" />
      <StatCard label="Applied" value={stats.applied} color="text-purple-600" />
      <StatCard
        label="Avg score"
        value={stats.avg_score ? `${stats.avg_score}/100` : "—"}
      />
      <StatCard
        label="Budget"
        value={`$${stats.budget_remaining_usd.toFixed(2)}`}
        color={stats.budget_remaining_usd < 1 ? "text-red-600" : "text-green-600"}
      />
    </div>
  );
}
