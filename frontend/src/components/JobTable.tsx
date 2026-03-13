"use client";

import Link from "next/link";
import type { Job } from "@/lib/types";
import { updateJobFeedback } from "@/lib/api";
import { ScoreBadge, StatusBadge, RemoteBadge } from "@/components/Badges";
import { ExternalLinkIcon, CheckIcon, CrossIcon } from "@/components/Icons";

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
      <div className="rounded border border-dashed border-border p-12 text-center">
        <p className="text-text-muted">
          Aucune offre trouvée. Vos offres apparaîtront au prochain cycle de scoring (toutes les 4 heures).
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded border border-border">
      <table className="min-w-full divide-y divide-border">
        <thead className="bg-surface-2">
          <tr>
            {hasSelection && (
              <th className="px-3 py-3">
                <input
                  type="checkbox"
                  checked={selected.size === jobs.length && jobs.length > 0}
                  onChange={onToggleSelectAll}
                  className="h-4 w-4 rounded border-border accent-amber"
                />
              </th>
            )}
            {["Score", "Titre", "Entreprise", "Lieu", "Source", "Statut", "Actions"].map((h) => (
              <th key={h} className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-surface-1">
          {jobs.map((job) => (
            <tr
              key={job.id}
              className={`transition-colors hover:bg-amber/5 ${
                hasSelection && selected.has(job.id) ? "border-l-2 border-l-amber bg-amber/5" : ""
              }`}
            >
              {hasSelection && (
                <td className="px-3 py-3">
                  <input
                    type="checkbox"
                    checked={selected.has(job.id)}
                    onChange={() => onToggleSelect(job.id)}
                    className="h-4 w-4 rounded border-border accent-amber"
                  />
                </td>
              )}
              <td className="px-4 py-3">
                <ScoreBadge score={job.match_score} priority={job.match_priority} />
              </td>
              <td className="px-4 py-3">
                <Link href={`/dashboard/${job.id}`} className="font-medium text-amber hover:text-amber-bright transition-colors">
                  {job.title}
                </Link>
              </td>
              <td className="px-4 py-3 text-sm text-text-secondary">{job.company}</td>
              <td className="px-4 py-3 text-sm">
                <span className="text-text-secondary">{job.location || "\u2014"}</span>{" "}
                <RemoteBadge type={job.remote_type} />
              </td>
              <td className="px-4 py-3 font-mono text-xs text-text-muted">{job.source}</td>
              <td className="px-4 py-3"><StatusBadge status={job.status} /></td>
              <td className="px-4 py-3">
                <div className="flex gap-1">
                  {job.status === "new" && (
                    <>
                      <button
                        onClick={() => handleFeedback(job.id, "interested")}
                        className="flex items-center gap-1 rounded bg-positive/10 px-2 py-1 text-xs text-positive hover:bg-positive/20 transition-colors"
                      >
                        <CheckIcon size={12} /> Intéressé
                      </button>
                      <button
                        onClick={() => handleFeedback(job.id, "rejected")}
                        className="flex items-center gap-1 rounded bg-surface-3 px-2 py-1 text-xs text-text-muted hover:bg-surface-3/80 transition-colors"
                      >
                        <CrossIcon size={12} /> Refuser
                      </button>
                    </>
                  )}
                  {job.source_url && (
                    <a
                      href={job.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 rounded bg-amber/10 px-2 py-1 text-xs text-amber hover:bg-amber/20 transition-colors"
                    >
                      <ExternalLinkIcon size={12} /> Voir
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
