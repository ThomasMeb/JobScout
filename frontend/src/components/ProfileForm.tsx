"use client";

import { useState, useMemo } from "react";
import type { Profile } from "@/lib/types";

interface ProfileFormProps {
  profile: Partial<Profile>;
  onSubmit: (data: Partial<Profile>) => Promise<void>;
  mode: "onboarding" | "settings";
}

const STEP_META = [
  { label: "Profil", time: "~1 min", required: true },
  { label: "Recherche", time: "~30s", required: true },
  { label: "Localisation", time: "~30s", required: true },
  { label: "Mots-clés", time: "~30s", required: false },
  { label: "Notifications", time: "~30s", required: false },
];

/** Extract likely keywords from pasted CV text. */
function extractKeywordsFromCV(cvText: string): string[] {
  if (!cvText || cvText.length < 50) return [];
  const text = cvText.toLowerCase();
  const techKeywords = [
    "python", "javascript", "typescript", "react", "next.js", "node.js",
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
    "postgresql", "mongodb", "redis", "elasticsearch",
    "machine learning", "deep learning", "nlp", "pytorch", "tensorflow",
    "scikit-learn", "pandas", "numpy", "spark", "airflow",
    "fastapi", "django", "flask", "express",
    "git", "ci/cd", "agile", "scrum",
    "java", "go", "rust", "c++", "scala", "kotlin",
    "sql", "graphql", "rest api", "microservices",
    "linux", "devops", "mlops", "data engineering",
  ];
  return techKeywords.filter((kw) => text.includes(kw));
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
    telegram_chat_id: profile.telegram_chat_id || "",
    min_score_notify: profile.min_score_notify ?? 70,
    monthly_budget_usd: profile.monthly_budget_usd ?? 5,
  });
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState("");

  function parseList(str: string): string[] {
    return str
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  /** Validate the current step. Returns true if valid. */
  function validateStep(s: number): boolean {
    const newErrors: Record<string, string> = {};
    if (s === 0) {
      if (!form.name.trim()) newErrors.name = "Le nom est requis";
      if (!form.cv_text.trim() || form.cv_text.trim().length < 50)
        newErrors.cv_text = "Veuillez coller votre CV (au moins 50 caractères)";
    } else if (s === 1) {
      if (!form.search_queries.trim())
        newErrors.search_queries = "Au moins une requête de recherche est requise";
    }
    // Steps 2-4 are optional or have defaults
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  function handleNext() {
    if (validateStep(step)) {
      setStep(step + 1);
    }
  }

  /** CV keyword suggestions — recompute when cv_text changes. */
  const suggestedKeywords = useMemo(
    () => extractKeywordsFromCV(form.cv_text),
    [form.cv_text]
  );

  function applySuggestions() {
    const current = parseList(form.bonus_keywords);
    const merged = [...new Set([...current, ...suggestedKeywords])];
    setForm({ ...form, bonus_keywords: merged.join(", ") });
  }

  async function handleSubmit() {
    if (!validateStep(step)) return;
    setSaving(true);
    setSubmitError("");
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
        telegram_chat_id: form.telegram_chat_id || null,
        min_score_notify: Number(form.min_score_notify),
        monthly_budget_usd: Number(form.monthly_budget_usd),
        ...(mode === "onboarding" ? { onboarding_completed: true } : {}),
      });
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Erreur lors de la sauvegarde. Veuillez réessayer.");
    } finally {
      setSaving(false);
    }
  }

  const inputClass = (field: string) =>
    `w-full rounded-lg border px-3 py-2 dark:bg-gray-800 ${
      errors[field]
        ? "border-red-400 focus:ring-red-400"
        : "border-gray-300 dark:border-gray-600"
    }`;

  const steps = [
    // Step 0: Name + CV
    <div key="cv" className="space-y-4">
      <h2 className="text-xl font-semibold">Votre profil</h2>
      <div>
        <label className="mb-1 block text-sm font-medium">Nom</label>
        <input
          type="text"
          value={form.name}
          onChange={(e) => {
            setForm({ ...form, name: e.target.value });
            if (errors.name) setErrors({ ...errors, name: "" });
          }}
          className={inputClass("name")}
          placeholder="Jean Dupont"
        />
        {errors.name && <p className="mt-1 text-xs text-red-500">{errors.name}</p>}
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">CV (collez le texte)</label>
        <textarea
          value={form.cv_text}
          onChange={(e) => {
            setForm({ ...form, cv_text: e.target.value });
            if (errors.cv_text) setErrors({ ...errors, cv_text: "" });
          }}
          rows={10}
          className={`${inputClass("cv_text")} font-mono text-sm`}
          placeholder="Collez le texte de votre CV ici..."
        />
        {errors.cv_text && <p className="mt-1 text-xs text-red-500">{errors.cv_text}</p>}
        {form.cv_text.length > 0 && (
          <p className="mt-1 text-xs text-gray-400">{form.cv_text.length} caractères</p>
        )}
      </div>
    </div>,

    // Step 1: Search queries
    <div key="queries" className="space-y-4">
      <h2 className="text-xl font-semibold">Recherche d&apos;emploi</h2>
      <div>
        <label className="mb-1 block text-sm font-medium">
          Requêtes de recherche (séparées par des virgules)
        </label>
        <input
          type="text"
          value={form.search_queries}
          onChange={(e) => {
            setForm({ ...form, search_queries: e.target.value });
            if (errors.search_queries) setErrors({ ...errors, search_queries: "" });
          }}
          className={inputClass("search_queries")}
          placeholder="Ingénieur ML, Data Scientist, Ingénieur IA"
        />
        {errors.search_queries && (
          <p className="mt-1 text-xs text-red-500">{errors.search_queries}</p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          Ces termes sont utilisés pour chercher sur les sites d&apos;emploi. Ajoutez tous les titres de poste pertinents.
        </p>
      </div>
    </div>,

    // Step 2: Locations + remote
    <div key="locations" className="space-y-4">
      <h2 className="text-xl font-semibold">Préférences de localisation</h2>
      <div>
        <label className="mb-1 block text-sm font-medium">
          Localisations (séparées par des virgules)
        </label>
        <input
          type="text"
          value={form.search_locations}
          onChange={(e) => setForm({ ...form, search_locations: e.target.value })}
          className={inputClass("search_locations")}
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
        <label htmlFor="remote" className="text-sm">Accepter les postes en télétravail</label>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Salaire minimum (EUR/an)</label>
        <input
          type="number"
          value={form.min_salary}
          onChange={(e) => setForm({ ...form, min_salary: e.target.value })}
          className={inputClass("min_salary")}
          placeholder="45000"
        />
      </div>
    </div>,

    // Step 3: Keywords (optional)
    <div key="keywords" className="space-y-4">
      <h2 className="text-xl font-semibold">
        Mots-clés
        <span className="ml-2 text-sm font-normal text-gray-400">(optionnel)</span>
      </h2>
      {suggestedKeywords.length > 0 && !form.bonus_keywords.trim() && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 dark:border-blue-800 dark:bg-blue-900/20">
          <p className="mb-2 text-sm font-medium text-blue-700 dark:text-blue-300">
            Mots-clés détectés dans votre CV :
          </p>
          <div className="mb-2 flex flex-wrap gap-1">
            {suggestedKeywords.slice(0, 12).map((kw) => (
              <span
                key={kw}
                className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700 dark:bg-blue-800 dark:text-blue-200"
              >
                {kw}
              </span>
            ))}
          </div>
          <button
            type="button"
            onClick={applySuggestions}
            className="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400"
          >
            Utiliser comme mots-clés bonus
          </button>
        </div>
      )}
      <div>
        <label className="mb-1 block text-sm font-medium">Mots-clés bonus</label>
        <input
          type="text"
          value={form.bonus_keywords}
          onChange={(e) => setForm({ ...form, bonus_keywords: e.target.value })}
          className={inputClass("bonus_keywords")}
          placeholder="python, machine learning, pytorch, docker"
        />
        <p className="mt-1 text-xs text-gray-500">Les offres contenant ces mots-clés obtiennent un bonus de score.</p>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Mots-clés pénalisants</label>
        <input
          type="text"
          value={form.penalty_keywords}
          onChange={(e) => setForm({ ...form, penalty_keywords: e.target.value })}
          className={inputClass("penalty_keywords")}
          placeholder="Java, .NET, 10+ years, PhD required"
        />
        <p className="mt-1 text-xs text-gray-500">Les offres contenant ces mots-clés reçoivent une pénalité de score.</p>
      </div>
    </div>,

    // Step 4: Notifications & Budget (optional)
    <div key="notifications" className="space-y-4">
      <h2 className="text-xl font-semibold">
        Notifications et budget
        <span className="ml-2 text-sm font-normal text-gray-400">(optionnel)</span>
      </h2>
      <div>
        <label className="mb-1 block text-sm font-medium">Email de notification</label>
        <input
          type="email"
          value={form.notification_email}
          onChange={(e) => setForm({ ...form, notification_email: e.target.value })}
          className={inputClass("notification_email")}
          placeholder="you@example.com"
        />
        <p className="mt-1 text-xs text-gray-500">
          Recevez un résumé par email quand de nouvelles offres à haut score sont trouvées. Laissez vide pour désactiver.
        </p>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Telegram Chat ID</label>
        <input
          type="text"
          value={form.telegram_chat_id}
          onChange={(e) => setForm({ ...form, telegram_chat_id: e.target.value })}
          className={inputClass("telegram_chat_id")}
          placeholder="123456789"
        />
        <p className="mt-1 text-xs text-gray-500">
          Recevez des notifications Telegram. Envoyez un message à @userinfobot pour trouver votre Chat ID. Laissez vide pour désactiver.
        </p>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Score minimum pour les notifications</label>
        <input
          type="number"
          value={form.min_score_notify}
          onChange={(e) => setForm({ ...form, min_score_notify: Number(e.target.value) })}
          min={0}
          max={100}
          className={inputClass("min_score_notify")}
          placeholder="70"
        />
        <p className="mt-1 text-xs text-gray-500">
          Seules les offres dépassant ce seuil seront incluses dans les résumés email.
        </p>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Budget IA mensuel (USD)</label>
        <input
          type="number"
          value={form.monthly_budget_usd}
          onChange={(e) => setForm({ ...form, monthly_budget_usd: Number(e.target.value) })}
          min={0}
          step={0.5}
          className={inputClass("monthly_budget_usd")}
          placeholder="5.00"
        />
        <p className="mt-1 text-xs text-gray-500">
          Limite mensuelle pour le scoring IA des offres. Le scoring se met en pause quand le budget est atteint. Par défaut : 5 $.
        </p>
      </div>
    </div>,
  ];

  if (mode === "settings") {
    return (
      <div className="space-y-6">
        {steps.map((s) => s)}
        {submitError && (
          <p className="text-sm text-red-500">{submitError}</p>
        )}
        <button
          onClick={handleSubmit}
          disabled={saving}
          className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? "Sauvegarde..." : "Enregistrer"}
        </button>
      </div>
    );
  }

  // Onboarding: step by step
  const isOptionalStep = !STEP_META[step]?.required;

  return (
    <div className="mx-auto max-w-lg space-y-6">
      {/* Header with time estimate */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>
          Étape {step + 1} sur {steps.length} — {STEP_META[step]?.label}
        </span>
        <span>{STEP_META[step]?.time}</span>
      </div>

      {/* Progress */}
      <div className="flex gap-2">
        {steps.map((_, i) => (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full transition-colors ${
              i <= step ? "bg-blue-600" : "bg-gray-200 dark:bg-gray-700"
            }`}
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
            Retour
          </button>
        ) : (
          <div />
        )}

        <div className="flex gap-2">
          {isOptionalStep && step < steps.length - 1 && (
            <button
              onClick={() => setStep(step + 1)}
              className="rounded-lg border border-gray-300 px-4 py-2 text-gray-500 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800"
            >
              Passer
            </button>
          )}

          {submitError && (
            <p className="text-sm text-red-500">{submitError}</p>
          )}

          {step < steps.length - 1 ? (
            <button
              onClick={handleNext}
              className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
            >
              Suivant
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={saving}
              className="rounded-lg bg-green-600 px-6 py-2 text-white hover:bg-green-700 disabled:opacity-50"
            >
              {saving ? "Sauvegarde..." : "Terminer la configuration"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
