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
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
        {title}
      </h3>
      <div className="flex items-end gap-1" style={{ height: 120 }}>
        {data.map((d) => (
          <div key={d.label} className="flex flex-1 flex-col items-center gap-1">
            <span className="text-[10px] text-gray-500">
              {d.value > 0 ? d.value : ""}
            </span>
            <div
              className="w-full rounded-t"
              style={{
                height: `${(d.value / max) * 100}%`,
                minHeight: d.value > 0 ? 4 : 0,
                backgroundColor: color,
              }}
            />
            <span className="text-[9px] text-gray-400 leading-tight text-center">
              {d.label}
            </span>
          </div>
        ))}
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
      <BarChart
        title="Répartition des scores"
        data={scoreBuckets}
        color="#3b82f6"
      />
      {dailyJobs.length > 0 && (
        <BarChart
          title="Offres analysées (30 derniers jours)"
          data={dailyJobs}
          color="#10b981"
        />
      )}
    </div>
  );
}
