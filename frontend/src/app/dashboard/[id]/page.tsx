"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import AppShell from "@/components/AppShell";
import { toast } from "sonner";
import { getJob, updateJobFeedback } from "@/lib/api";
import type { Job } from "@/lib/types";
import { ArrowLeftIcon, ExternalLinkIcon, CheckIcon, CrossIcon, PenIcon } from "@/components/Icons";

function ScoreRing({ score }: { score: number }) {
  const r = 52;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 70 ? "var(--positive)" : score >= 40 ? "var(--amber)" : "var(--negative)";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="130" height="130" viewBox="0 0 130 130">
        <circle cx="65" cy="65" r={r} fill="none" stroke="var(--border)" strokeWidth="6" />
        <circle
          cx="65" cy="65" r={r} fill="none"
          stroke={color} strokeWidth="6"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          className="score-ring"
          transform="rotate(-90 65 65)"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="font-mono text-4xl font-bold text-text-primary" style={{ letterSpacing: "-0.04em" }}>{Math.round(score)}</span>
        <span className="text-[10px] uppercase tracking-widest text-text-muted">score</span>
      </div>
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
      const labels: Record<string, string> = { interested: "Intéressé", applied: "Postulé", rejected: "Refusé" };
      toast.success(labels[status] || "Mis à jour");
    } catch (e) {
      console.error(e);
      toast.error("Erreur lors de la mise à jour");
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
            <div className="flex items-start justify-between gap-6">
              <div className="flex-1">
                <h1 className="font-display text-3xl italic text-text-primary sm:text-4xl" style={{ letterSpacing: "-0.02em" }}>
                  {job.title}
                </h1>
                <p className="mt-2 text-lg text-text-secondary">
                  {job.company} &middot; {job.location || "Lieu non renseigné"}
                </p>
                <div className="editorial-divider mt-3 w-12" />
              </div>
              {job.match_score !== null && <ScoreRing score={job.match_score} />}
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-2">
              <span className="tag-pill font-mono">{job.source}</span>
              <span className="tag-pill">
                {job.remote_type === "full" ? "Télétravail" : job.remote_type === "partial" ? "Hybride" : "Sur site"}
              </span>
              {job.salary_min && (
                <span className="tag-pill font-mono">
                  {job.salary_min}{job.salary_max ? `–${job.salary_max}` : "+"} {job.salary_currency}
                </span>
              )}
              <span className={`rounded px-3 py-1 text-xs font-medium ${st.bg}`}>{st.label}</span>
            </div>

            {/* Scoring breakdown */}
            {job.match_reasoning && (
              <div className="rounded border border-border bg-surface-1 p-5">
                <h2 className="label mb-3">Détail du scoring IA</h2>
                <pre className="whitespace-pre-wrap font-mono text-sm text-text-secondary leading-relaxed">{job.match_reasoning}</pre>
                {job.match_keywords.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    {job.match_keywords.map((kw, i) => (
                      <span key={i} className="rounded bg-positive/10 px-2.5 py-0.5 text-xs font-medium text-positive">{kw}</span>
                    ))}
                  </div>
                )}
                {job.missing_keywords.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {job.missing_keywords.map((kw, i) => (
                      <span key={i} className="rounded bg-negative/10 px-2.5 py-0.5 text-xs font-medium text-negative">{kw}</span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Notes + Actions */}
            <div className="rounded border border-border bg-surface-1 p-5">
              <h2 className="label mb-3">Notes</h2>
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
                <h2 className="label mb-3">Tags</h2>
                <div className="flex flex-wrap gap-1.5">
                  {job.tags.map((tag, i) => (
                    <span key={i} className="tag-pill">{tag}</span>
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
