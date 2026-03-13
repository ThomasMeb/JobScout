"use client";

import Link from "next/link";
import type { Job } from "@/lib/types";
import { updateJobFeedback } from "@/lib/api";
import { ScoreBadge, StatusBadge, RemoteBadge } from "@/components/Badges";

export default function JobTable({
  jobs,
  onRefresh,
  selected,
  onToggleSelect,
  onToggleSelectAll,
}: {
  jobs: Job[];
  onRefresh: () => void;
  selected?: Set<number>;
  onToggleSelect?: (id: number) => void;
  onToggleSelectAll?: () => void;
}) {
  async function handleFeedback(jobId: number, status: string) {
    try {
      await updateJobFeedback(jobId, status);
      onRefresh();
    } catch (e) {
      console.error("Feedback error:", e);
    }
  }

  const hasSelection = selected !== undefined && onToggleSelect !== undefined;

  if (!jobs.length) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 p-12 text-center dark:border-gray-600">
        <p className="text-gray-500 dark:text-gray-400">
          Aucune offre trouvée. Vos offres apparaîtront au prochain cycle de scoring (toutes les 4 heures).
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            {hasSelection && (
              <th className="px-3 py-3">
                <input
                  type="checkbox"
                  checked={selected.size === jobs.length && jobs.length > 0}
                  onChange={onToggleSelectAll}
                  className="h-4 w-4 rounded border-gray-300"
                />
              </th>
            )}
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Titre</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Entreprise</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Lieu</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
          {jobs.map((job) => (
            <tr
              key={job.id}
              className={`hover:bg-gray-50 dark:hover:bg-gray-800 ${
                hasSelection && selected.has(job.id) ? "bg-blue-50 dark:bg-blue-950" : ""
              }`}
            >
              {hasSelection && (
                <td className="px-3 py-3">
                  <input
                    type="checkbox"
                    checked={selected.has(job.id)}
                    onChange={() => onToggleSelect(job.id)}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                </td>
              )}
              <td className="px-4 py-3">
                <ScoreBadge score={job.match_score} priority={job.match_priority} />
              </td>
              <td className="px-4 py-3">
                <Link
                  href={`/dashboard/${job.id}`}
                  className="font-medium text-blue-600 hover:underline dark:text-blue-400"
                >
                  {job.title}
                </Link>
              </td>
              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                {job.company}
              </td>
              <td className="px-4 py-3 text-sm">
                <span className="text-gray-600 dark:text-gray-400">{job.location || "\u2014"}</span>
                {" "}
                <RemoteBadge type={job.remote_type} />
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">{job.source}</td>
              <td className="px-4 py-3">
                <StatusBadge status={job.status} />
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-1">
                  {job.status === "new" && (
                    <>
                      <button
                        onClick={() => handleFeedback(job.id, "interested")}
                        className="rounded bg-green-100 px-2 py-1 text-xs text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300"
                      >
                        Intéressé
                      </button>
                      <button
                        onClick={() => handleFeedback(job.id, "rejected")}
                        className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400"
                      >
                        Refuser
                      </button>
                    </>
                  )}
                  {job.source_url && (
                    <a
                      href={job.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded bg-blue-100 px-2 py-1 text-xs text-blue-700 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-300"
                    >
                      Voir
                    </a>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
