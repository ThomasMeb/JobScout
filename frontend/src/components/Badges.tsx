"use client";

export function ScoreBadge({ score, priority }: { score: number | null; priority: string }) {
  if (score === null) return <span className="text-text-muted">&mdash;</span>;

  const colors: Record<string, string> = {
    high: "bg-positive/15 text-positive",
    medium: "bg-amber/15 text-amber-bright",
    low: "bg-negative/15 text-negative",
  };

  return (
    <span className={`inline-flex items-center gap-1.5 rounded px-2.5 py-0.5 font-mono text-xs font-medium ${colors[priority] || colors.low}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${priority === "high" ? "bg-positive" : priority === "medium" ? "bg-amber" : "bg-negative"}`} />
      {Math.round(score)}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { bg: string; dot: string }> = {
    new: { bg: "bg-info/10 text-info", dot: "bg-info" },
    interested: { bg: "bg-positive/10 text-positive", dot: "bg-positive" },
    applied: { bg: "bg-purple/10 text-purple", dot: "bg-purple" },
    rejected: { bg: "bg-surface-3 text-text-muted", dot: "bg-text-muted" },
  };

  const labels: Record<string, string> = {
    new: "Nouveau",
    interested: "Intéressé",
    applied: "Postulé",
    rejected: "Refusé",
  };

  const c = config[status] || config.new;

  return (
    <span className={`inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-xs font-medium ${c.bg}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {labels[status] || status}
    </span>
  );
}

export function RemoteBadge({ type }: { type: string }) {
  if (type === "full") return <span className="text-xs text-positive">Télétravail</span>;
  if (type === "partial") return <span className="text-xs text-info">Hybride</span>;
  return <span className="text-xs text-text-muted">Sur site</span>;
}
