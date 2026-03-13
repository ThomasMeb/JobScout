"use client";

import type { UserStats } from "@/lib/types";
import { TargetIcon, ZapIcon, CheckIcon, PenIcon, ChartIcon, CreditCardIcon } from "@/components/Icons";

const STATS_CONFIG = [
  { key: "total_jobs", label: "Total offres", icon: TargetIcon, borderColor: "border-l-text-secondary" },
  { key: "new_jobs", label: "Nouvelles", icon: ZapIcon, borderColor: "border-l-info" },
  { key: "interested", label: "Intéressé", icon: CheckIcon, borderColor: "border-l-positive" },
  { key: "applied", label: "Postulé", icon: PenIcon, borderColor: "border-l-purple" },
  { key: "avg_score", label: "Score moy.", icon: ChartIcon, borderColor: "border-l-amber" },
  { key: "budget_remaining_usd", label: "Budget", icon: CreditCardIcon, borderColor: "border-l-positive" },
] as const;

function formatValue(key: string, stats: UserStats): string {
  if (key === "avg_score") return stats.avg_score ? `${stats.avg_score}` : "—";
  if (key === "budget_remaining_usd") return `${stats.budget_remaining_usd.toFixed(2)} $`;
  return String(stats[key as keyof UserStats]);
}

export default function StatsBar({ stats }: { stats: UserStats }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
      {STATS_CONFIG.map(({ key, label, icon: IconComponent, borderColor }) => {
        const budgetLow = key === "budget_remaining_usd" && stats.budget_remaining_usd < 1;
        return (
          <div
            key={key}
            className={`rounded border border-border border-l-2 ${budgetLow ? "border-l-negative" : borderColor} bg-surface-1 p-4`}
          >
            <div className="flex items-center gap-2 text-text-muted">
              <IconComponent size={14} />
              <span className="text-xs uppercase tracking-wider">{label}</span>
            </div>
            <p className={`mt-2 font-mono text-2xl font-bold ${budgetLow ? "text-negative" : "text-text-primary"}`}>
              {formatValue(key, stats)}
            </p>
          </div>
        );
      })}
    </div>
  );
}
