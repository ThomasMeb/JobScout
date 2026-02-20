"use client";

import { useState } from "react";
import type { Profile } from "@/lib/types";

interface ProfileFormProps {
  profile: Partial<Profile>;
  onSubmit: (data: Partial<Profile>) => Promise<void>;
  mode: "onboarding" | "settings";
}

export default function ProfileForm({ profile, onSubmit, mode }: ProfileFormProps) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    name: profile.name || "",
    cv_text: profile.cv_text || "",
    search_queries: (profile.search_queries || []).join(", "),
    search_locations: (profile.search_locations || []).join(", "),
    remote_accepted: profile.remote_accepted ?? true,
    min_salary: profile.min_salary || "",
    bonus_keywords: (profile.bonus_keywords || []).join(", "),
    penalty_keywords: (profile.penalty_keywords || []).join(", "),
    notification_email: profile.notification_email || "",
    min_score_notify: profile.min_score_notify ?? 70,
    monthly_budget_usd: profile.monthly_budget_usd ?? 5,
  });
  const [saving, setSaving] = useState(false);

  function parseList(str: string): string[] {
    return str
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  async function handleSubmit() {
    setSaving(true);
    try {
      await onSubmit({
        name: form.name,
        cv_text: form.cv_text,
        search_queries: parseList(form.search_queries),
        search_locations: parseList(form.search_locations),
        remote_accepted: form.remote_accepted,
        min_salary: form.min_salary ? Number(form.min_salary) : null,
        bonus_keywords: parseList(form.bonus_keywords),
        penalty_keywords: parseList(form.penalty_keywords),
        notification_email: form.notification_email || null,
        min_score_notify: Number(form.min_score_notify),
        monthly_budget_usd: Number(form.monthly_budget_usd),
        ...(mode === "onboarding" ? { onboarding_completed: true } : {}),
      });
    } finally {
      setSaving(false);
    }
  }

  const steps = [
    // Step 0: Name + CV
    <div key="cv" className="space-y-4">
      <h2 className="text-xl font-semibold">Your profile</h2>
      <div>
        <label className="mb-1 block text-sm font-medium">Name</label>
        <input
          type="text"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800"
          placeholder="John Doe"
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">CV / Resume (paste text)</label>
        <textarea
          value={form.cv_text}
          onChange={(e) => setForm({ ...form, cv_text: e.target.value })}
          rows={10}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm dark:border-gray-600 dark:bg-gray-800"
          placeholder="Paste your CV text here..."
        />
      </div>
    </div>,

    // Step 1: Search queries
    <div key="queries" className="space-y-4">
      <h2 className="text-xl font-semibold">Job search</h2>
      <div>
        <label className="mb-1 block text-sm font-medium">
          Search queries (comma-separated)
        </label>
        <input
          type="text"
          value={form.search_queries}
          onChange={(e) => setForm({ ...form, search_queries: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800"
          placeholder="ML Engineer, Data Scientist, AI Engineer"
        />
        <p className="mt-1 text-xs text-gray-500">
          These are used to search job boards. Add all relevant job titles.
        </p>
      </div>
    </div>,

    // Step 2: Locations + remote
    <div key="locations" className="space-y-4">
      <h2 className="text-xl font-semibold">Location preferences</h2>
      <div>
        <label className="mb-1 block text-sm font-medium">
          Locations (comma-separated)
        </label>
        <input
          type="text"
          value={form.search_locations}
          onChange={(e) => setForm({ ...form, search_locations: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800"
          placeholder="Paris, Lille, France"
        />
      </div>
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="remote"
          checked={form.remote_accepted}
          onChange={(e) => setForm({ ...form, remote_accepted: e.target.checked })}
          className="h-4 w-4 rounded border-gray-300"
        />
        <label htmlFor="remote" className="text-sm">Accept remote positions</label>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Minimum salary (EUR/year)</label>
        <input
          type="number"
          value={form.min_salary}
          onChange={(e) => setForm({ ...form, min_salary: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800"
          placeholder="45000"
        />
      </div>
    </div>,

    // Step 3: Keywords
    <div key="keywords" className="space-y-4">
      <h2 className="text-xl font-semibold">Keywords (optional)</h2>
      <div>
        <label className="mb-1 block text-sm font-medium">Bonus keywords</label>
        <input
          type="text"
          value={form.bonus_keywords}
          onChange={(e) => setForm({ ...form, bonus_keywords: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800"
          placeholder="python, machine learning, pytorch, docker"
        />
        <p className="mt-1 text-xs text-gray-500">Jobs with these keywords get a score boost.</p>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Penalty keywords</label>
        <input
          type="text"
          value={form.penalty_keywords}
          onChange={(e) => setForm({ ...form, penalty_keywords: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800"
          placeholder="Java, .NET, 10+ years, PhD required"
        />
        <p className="mt-1 text-xs text-gray-500">Jobs with these keywords get a score penalty.</p>
      </div>
    </div>,

    // Step 4: Notifications & Budget
    <div key="notifications" className="space-y-4">
      <h2 className="text-xl font-semibold">Notifications & budget</h2>
      <div>
        <label className="mb-1 block text-sm font-medium">Notification email</label>
        <input
          type="email"
          value={form.notification_email}
          onChange={(e) => setForm({ ...form, notification_email: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800"
          placeholder="you@example.com"
        />
        <p className="mt-1 text-xs text-gray-500">
          Receive email digests when new high-scoring jobs are found. Leave empty to disable.
        </p>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Minimum score for notifications</label>
        <input
          type="number"
          value={form.min_score_notify}
          onChange={(e) => setForm({ ...form, min_score_notify: Number(e.target.value) })}
          min={0}
          max={100}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800"
          placeholder="70"
        />
        <p className="mt-1 text-xs text-gray-500">
          Only jobs scoring above this threshold will be included in email digests.
        </p>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Monthly AI budget (USD)</label>
        <input
          type="number"
          value={form.monthly_budget_usd}
          onChange={(e) => setForm({ ...form, monthly_budget_usd: Number(e.target.value) })}
          min={0}
          step={0.5}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800"
          placeholder="5.00"
        />
        <p className="mt-1 text-xs text-gray-500">
          Monthly limit for AI job scoring. Scoring pauses when the budget is reached. Default: $5.
        </p>
      </div>
    </div>,
  ];

  if (mode === "settings") {
    return (
      <div className="space-y-6">
        {steps.map((s) => s)}
        <button
          onClick={handleSubmit}
          disabled={saving}
          className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save settings"}
        </button>
      </div>
    );
  }

  // Onboarding: step by step
  return (
    <div className="mx-auto max-w-lg space-y-6">
      {/* Progress */}
      <div className="flex gap-2">
        {steps.map((_, i) => (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full ${i <= step ? "bg-blue-600" : "bg-gray-200 dark:bg-gray-700"}`}
          />
        ))}
      </div>

      {steps[step]}

      <div className="flex justify-between">
        {step > 0 ? (
          <button
            onClick={() => setStep(step - 1)}
            className="rounded-lg border border-gray-300 px-4 py-2 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800"
          >
            Back
          </button>
        ) : (
          <div />
        )}

        {step < steps.length - 1 ? (
          <button
            onClick={() => setStep(step + 1)}
            className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
          >
            Next
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="rounded-lg bg-green-600 px-6 py-2 text-white hover:bg-green-700 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Complete setup"}
          </button>
        )}
      </div>
    </div>
  );
}
