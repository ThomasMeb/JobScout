"use client";

import type { UserStats } from "@/lib/types";
import { TargetIcon, ZapIcon, CheckIcon, PenIcon, ChartIcon, CreditCardIcon } from "@/components/Icons";

const STATS_CONFIG = [
  { key: "total_jobs", label: "Total offres", icon: TargetIcon, accent: "text-text-primary" },
  { key: "new_jobs", label: "Nouvelles", icon: ZapIcon, accent: "text-info" },
  { key: "interested", label: "Intéressé", icon: CheckIcon, accent: "text-positive" },
  { key: "applied", label: "Postulé", icon: PenIcon, accent: "text-purple" },
  { key: "avg_score", label: "Score moy.", icon: ChartIcon, accent: "text-amber-bright" },
  { key: "budget_remaining_usd", label: "Budget", icon: CreditCardIcon, accent: "text-positive" },
] as const;

function formatValue(key: string, stats: UserStats): string {
  if (key === "avg_score") return stats.avg_score ? `${stats.avg_score}` : "—";
  if (key === "budget_remaining_usd") return `${stats.budget_remaining_usd.toFixed(2)} $`;
  return String(stats[key as keyof UserStats]);
}

export default function StatsBar({ stats }: { stats: UserStats }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
      {STATS_CONFIG.map(({ key, label, icon: IconComponent, accent }) => {
        const budgetLow = key === "budget_remaining_usd" && stats.budget_remaining_usd < 1;
        return (
          <div
            key={key}
            className="rounded border border-border bg-surface-1 p-4 transition-colors hover:border-border-hover"
          >
            <div className="flex items-center gap-2 text-text-muted">
              <IconComponent size={14} />
              <span className="label">{label}</span>
            </div>
            <p className={`mt-2 font-mono text-3xl font-bold ${budgetLow ? "text-negative" : accent}`} style={{ letterSpacing: "-0.04em" }}>
              {formatValue(key, stats)}
            </p>
          </div>
        );
      })}
    </div>
  );
}
