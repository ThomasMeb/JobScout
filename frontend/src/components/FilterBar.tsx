"use client";

import { useState } from "react";

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
    "w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800 sm:w-auto";

  const filters = (
    <>
      <select
        value={statusFilter}
        onChange={(e) => { setStatusFilter(e.target.value); onPageReset(); }}
        className={selectClass}
      >
        <option value="">Tous les statuts</option>
        <option value="new">Nouveau</option>
        <option value="interested">Intéressé</option>
        <option value="applied">Postulé</option>
        <option value="rejected">Refusé</option>
      </select>

      <select
        value={minScore === "" ? "" : String(minScore)}
        onChange={(e) => { setMinScore(e.target.value ? Number(e.target.value) : ""); onPageReset(); }}
        className={selectClass}
      >
        <option value="">Tout score</option>
        <option value="70">70+</option>
        <option value="50">50+</option>
        <option value="30">30+</option>
      </select>

      <select
        value={sourceFilter}
        onChange={(e) => { setSourceFilter(e.target.value); onPageReset(); }}
        className={selectClass}
      >
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
          className="flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 010 2H4a1 1 0 01-1-1zm4 6a1 1 0 011-1h8a1 1 0 010 2H8a1 1 0 01-1-1zm2 6a1 1 0 011-1h4a1 1 0 010 2h-4a1 1 0 01-1-1z" />
          </svg>
          Filtres{activeCount > 0 ? ` (${activeCount})` : ""}
        </button>
        <span className="text-sm text-gray-500">
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
        <span className="text-sm text-gray-500">
          {total} offre{total !== 1 ? "s" : ""}
        </span>
      </div>
    </div>
  );
}
