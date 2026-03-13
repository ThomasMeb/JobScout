"use client";

import { useState } from "react";
import { FilterIcon } from "@/components/Icons";

const SOURCES = [
  { value: "", label: "Toutes les sources" },
  { value: "wttj", label: "WTTJ" },
  { value: "remoteok", label: "RemoteOK" },
  { value: "adzuna", label: "Adzuna" },
  { value: "francetravail", label: "France Travail" },
  { value: "jobspy", label: "JobSpy" },
  { value: "hellowork", label: "HelloWork" },
  { value: "apec", label: "APEC" },
  { value: "freework", label: "FreeWork" },
  { value: "welovedevs", label: "WeLoveDevs" },
];

export default function FilterBar({
  statusFilter,
  setStatusFilter,
  minScore,
  setMinScore,
  sourceFilter,
  setSourceFilter,
  total,
  onPageReset,
}: {
  statusFilter: string;
  setStatusFilter: (v: string) => void;
  minScore: number | "";
  setMinScore: (v: number | "") => void;
  sourceFilter: string;
  setSourceFilter: (v: string) => void;
  total: number;
  onPageReset: () => void;
}) {
  const [open, setOpen] = useState(false);
  const activeCount = [statusFilter, minScore, sourceFilter].filter(Boolean).length;

  const selectClass =
    "w-full rounded border border-border bg-surface-1 px-3 py-1.5 text-sm text-text-primary focus:border-amber focus:outline-none focus:ring-1 focus:ring-amber transition-colors sm:w-auto";

  const filters = (
    <>
      <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); onPageReset(); }} className={selectClass}>
        <option value="">Tous les statuts</option>
        <option value="new">Nouveau</option>
        <option value="interested">Intéressé</option>
        <option value="applied">Postulé</option>
        <option value="rejected">Refusé</option>
      </select>
      <select value={minScore === "" ? "" : String(minScore)} onChange={(e) => { setMinScore(e.target.value ? Number(e.target.value) : ""); onPageReset(); }} className={selectClass}>
        <option value="">Tout score</option>
        <option value="70">70+</option>
        <option value="50">50+</option>
        <option value="30">30+</option>
      </select>
      <select value={sourceFilter} onChange={(e) => { setSourceFilter(e.target.value); onPageReset(); }} className={selectClass}>
        {SOURCES.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>
    </>
  );

  return (
    <div>
      {/* Mobile: toggle button */}
      <div className="flex items-center justify-between md:hidden">
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-2 rounded border border-border px-3 py-1.5 text-sm text-text-secondary hover:border-border-hover hover:text-text-primary transition-colors"
        >
          <FilterIcon size={14} />
          Filtres{activeCount > 0 && (
            <span className="rounded bg-amber/10 px-1.5 py-0.5 text-xs font-medium text-amber">{activeCount}</span>
          )}
        </button>
        <span className="font-mono text-sm text-text-muted">
          {total} offre{total !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Mobile: collapsible filters */}
      {open && (
        <div className="mt-2 grid grid-cols-1 gap-2 md:hidden">
          {filters}
        </div>
      )}

      {/* Desktop: inline filters */}
      <div className="hidden items-center gap-3 md:flex">
        {filters}
        <span className="font-mono text-sm text-text-muted">
          {total} offre{total !== 1 ? "s" : ""}
        </span>
      </div>
    </div>
  );
}
