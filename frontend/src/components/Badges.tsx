"use client";

export function ScoreBadge({ score, priority }: { score: number | null; priority: string }) {
  if (score === null) return <span className="text-gray-400">&mdash;</span>;

  const colors: Record<string, string> = {
    high: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    low: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  };

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[priority] || colors.low}`}>
      {Math.round(score)}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    new: "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
    interested: "bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300",
    applied: "bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
    rejected: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
  };

  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors[status] || colors.new}`}>
      {{ new: "Nouveau", interested: "Intéressé", applied: "Postulé", rejected: "Refusé" }[status] || status}
    </span>
  );
}

export function RemoteBadge({ type }: { type: string }) {
  if (type === "full") return <span className="text-xs text-green-600 dark:text-green-400">Télétravail</span>;
  if (type === "partial") return <span className="text-xs text-blue-600 dark:text-blue-400">Hybride</span>;
  return <span className="text-xs text-gray-500 dark:text-gray-400">Sur site</span>;
}
