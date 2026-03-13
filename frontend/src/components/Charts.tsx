"use client";

import { useEffect, useState } from "react";
import { getChartData } from "@/lib/api";
import type { ChartData } from "@/lib/types";

function BarChart({
  title,
  data,
  color,
}: {
  title: string;
  data: { label: string; value: number }[];
  color: string;
}) {
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="rounded border border-border bg-surface-1 p-4">
      <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-text-muted">
        {title}
      </h3>
      {/* Grid lines */}
      <div className="relative" style={{ height: 120 }}>
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="border-t border-border/50" />
          ))}
        </div>
        <div className="relative flex items-end gap-1 h-full">
          {data.map((d) => (
            <div key={d.label} className="flex flex-1 flex-col items-center gap-1 h-full justify-end">
              <span className="font-mono text-[10px] text-text-muted">
                {d.value > 0 ? d.value : ""}
              </span>
              <div
                className="w-full rounded-t transition-all duration-500"
                style={{
                  height: `${(d.value / max) * 100}%`,
                  minHeight: d.value > 0 ? 4 : 0,
                  background: `linear-gradient(to top, ${color}, ${color}aa)`,
                }}
              />
              <span className="text-[9px] text-text-muted leading-tight text-center">
                {d.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Charts() {
  const [data, setData] = useState<ChartData | null>(null);

  useEffect(() => {
    getChartData()
      .then(setData)
      .catch(() => {});
  }, []);

  if (!data) return null;

  const scoreBuckets = Object.entries(data.score_buckets).map(
    ([label, value]) => ({ label, value })
  );

  const dailyJobs = data.daily_jobs.map((d) => ({
    label: d.date.slice(5),
    value: d.count,
  }));

  if (scoreBuckets.every((b) => b.value === 0) && dailyJobs.length === 0) {
    return null;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <BarChart title="Répartition des scores" data={scoreBuckets} color="#F59E0B" />
      {dailyJobs.length > 0 && (
        <BarChart title="Offres analysées (30 derniers jours)" data={dailyJobs} color="#34D399" />
      )}
    </div>
  );
}
