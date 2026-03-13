"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import AppShell from "@/components/AppShell";
import { getJob, updateJobFeedback } from "@/lib/api";
import type { Job } from "@/lib/types";
import { ArrowLeftIcon, ExternalLinkIcon, CheckIcon, CrossIcon, PenIcon } from "@/components/Icons";

function ScoreRing({ score }: { score: number }) {
  const r = 40;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 70 ? "#34D399" : score >= 40 ? "#F59E0B" : "#F87171";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#27272A" strokeWidth="6" />
        <circle
          cx="50" cy="50" r={r} fill="none"
          stroke={color} strokeWidth="6"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          className="score-ring"
          transform="rotate(-90 50 50)"
        />
      </svg>
      <span className="absolute font-mono text-2xl font-bold text-text-primary">{Math.round(score)}</span>
    </div>
  );
}

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    getJob(Number(id))
      .then((j) => { setJob(j); setNotes(j.user_notes || ""); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  async function handleFeedback(status: string) {
    if (!job) return;
    try {
      const updated = await updateJobFeedback(job.id, status, notes || undefined);
      setJob(updated);
    } catch (e) {
      console.error(e);
    }
  }

  if (loading) {
    return (
      <AuthGuard>
        <AppShell>
          <div className="flex min-h-[50vh] items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber border-t-transparent" />
          </div>
        </AppShell>
      </AuthGuard>
    );
  }

  if (!job) {
    return (
      <AuthGuard>
        <AppShell>
          <div className="flex min-h-[50vh] items-center justify-center">
            <p className="text-text-muted">Offre non trouvée</p>
          </div>
        </AppShell>
      </AuthGuard>
    );
  }

  const statusConfig: Record<string, { bg: string; label: string }> = {
    new: { bg: "bg-info/10 text-info", label: "Nouveau" },
    interested: { bg: "bg-positive/10 text-positive", label: "Intéressé" },
    applied: { bg: "bg-purple/10 text-purple", label: "Postulé" },
    rejected: { bg: "bg-surface-3 text-text-muted", label: "Refusé" },
  };
  const st = statusConfig[job.status] || statusConfig.new;

  return (
    <AuthGuard>
      <AppShell>
        <div className="px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl space-y-6">
            {/* Back */}
            <button onClick={() => router.back()} className="flex items-center gap-2 text-sm text-text-muted hover:text-text-primary transition-colors">
              <ArrowLeftIcon size={16} /> Retour
            </button>

            {/* Header */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight" style={{ letterSpacing: "-0.03em" }}>{job.title}</h1>
                <p className="mt-1 text-lg text-text-secondary">
                  {job.company} &middot; {job.location || "Lieu non renseigné"}
                </p>
              </div>
              {job.match_score !== null && <ScoreRing score={job.match_score} />}
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-2">
              <span className="rounded border border-border bg-surface-2 px-3 py-1 font-mono text-xs">{job.source}</span>
              <span className="rounded border border-border bg-surface-2 px-3 py-1 text-xs">
                {job.remote_type === "full" ? "Télétravail" : job.remote_type === "partial" ? "Hybride" : "Sur site"}
              </span>
              {job.salary_min && (
                <span className="rounded border border-border bg-surface-2 px-3 py-1 text-xs">
                  {job.salary_min}{job.salary_max ? `-${job.salary_max}` : "+"} {job.salary_currency}
                </span>
              )}
              <span className={`rounded px-3 py-1 text-xs font-medium ${st.bg}`}>{st.label}</span>
            </div>

            {/* Scoring breakdown */}
            {job.match_reasoning && (
              <div className="rounded border border-border bg-surface-1 p-5">
                <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-text-muted">Détail du scoring IA</h2>
                <pre className="whitespace-pre-wrap font-mono text-sm text-text-secondary leading-relaxed">{job.match_reasoning}</pre>
                {job.match_keywords.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    {job.match_keywords.map((kw, i) => (
                      <span key={i} className="rounded bg-positive/10 px-2 py-0.5 text-xs text-positive">{kw}</span>
                    ))}
                  </div>
                )}
                {job.missing_keywords.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {job.missing_keywords.map((kw, i) => (
                      <span key={i} className="rounded bg-negative/10 px-2 py-0.5 text-xs text-negative">{kw}</span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Notes + Actions */}
            <div className="rounded border border-border bg-surface-1 p-5">
              <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-text-muted">Notes</h2>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full rounded border border-border bg-surface-2 px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-amber focus:outline-none focus:ring-1 focus:ring-amber transition-colors"
                placeholder="Ajoutez vos notes personnelles sur cette offre..."
              />
              <div className="mt-4 flex flex-wrap gap-2">
                <button onClick={() => handleFeedback("interested")} className="flex items-center gap-1.5 rounded bg-positive px-4 py-2 text-sm font-medium text-surface-0 hover:brightness-110 transition">
                  <CheckIcon size={14} /> Intéressé
                </button>
                <button onClick={() => handleFeedback("applied")} className="flex items-center gap-1.5 rounded bg-purple px-4 py-2 text-sm font-medium text-surface-0 hover:brightness-110 transition">
                  <PenIcon size={14} /> Postulé
                </button>
                <button onClick={() => handleFeedback("rejected")} className="flex items-center gap-1.5 rounded bg-surface-3 px-4 py-2 text-sm font-medium text-text-secondary hover:bg-border-hover transition-colors">
                  <CrossIcon size={14} /> Refuser
                </button>
                {job.source_url && (
                  <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 rounded border border-amber/30 px-4 py-2 text-sm font-medium text-amber hover:bg-amber/10 transition-colors">
                    <ExternalLinkIcon size={14} /> Voir l&apos;original
                  </a>
                )}
                {job.apply_url && (
                  <a href={job.apply_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 rounded bg-amber px-4 py-2 text-sm font-medium text-surface-0 hover:bg-amber-bright transition-colors">
                    Postuler
                  </a>
                )}
              </div>
            </div>

            {/* Tags */}
            {job.tags.length > 0 && (
              <div className="rounded border border-border bg-surface-1 p-5">
                <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-text-muted">Tags</h2>
                <div className="flex flex-wrap gap-1.5">
                  {job.tags.map((tag, i) => (
                    <span key={i} className="rounded border border-border bg-surface-2 px-2.5 py-0.5 text-xs text-text-secondary">{tag}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
