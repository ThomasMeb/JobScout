"use client";

import { useEffect, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import AppShell from "@/components/AppShell";
import { createCheckout, createPortal, getBillingStatus, getProfile, getStats } from "@/lib/api";
import { CheckIcon, CreditCardIcon } from "@/components/Icons";
import type { UserStats } from "@/lib/types";

interface BillingInfo {
  plan: string;
  has_subscription: boolean;
  plan_expires_at: string | null;
  trial_started_at: string | null;
}

export default function BillingPage() {
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [profilePlan, setProfilePlan] = useState<string>("free");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    Promise.all([getBillingStatus(), getStats(), getProfile()])
      .then(([b, s, p]) => { setBilling(b); setStats(s); setProfilePlan(p.plan || "free"); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function handleUpgrade() {
    setActionLoading(true);
    try {
      const { checkout_url } = await createCheckout();
      if (checkout_url) window.location.href = checkout_url;
    } catch (e) { console.error("Checkout failed:", e); }
    setActionLoading(false);
  }

  async function handleManage() {
    setActionLoading(true);
    try {
      const { portal_url } = await createPortal();
      if (portal_url) window.location.href = portal_url;
    } catch (e) { console.error("Portal failed:", e); }
    setActionLoading(false);
  }

  const isPro = profilePlan === "pro";
  const isTrial = profilePlan === "trial";

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

  return (
    <AuthGuard>
      <AppShell>
        <div className="px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl space-y-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight" style={{ letterSpacing: "-0.03em" }}>Abonnement</h1>
              <p className="mt-1 text-sm text-text-secondary">Gérez votre plan et votre utilisation.</p>
            </div>

            {/* Current Plan */}
            <div className={`rounded border p-6 ${isPro ? "border-amber/30 bg-amber/5" : "border-border bg-surface-1"}`}>
              <div className="flex items-center gap-2 mb-3">
                <CreditCardIcon size={18} className="text-amber" />
                <h2 className="text-lg font-semibold">Plan actuel</h2>
              </div>
              <div className="flex items-center gap-3">
                <span className={`inline-block rounded px-3 py-1 font-mono text-sm font-medium ${
                  isPro ? "bg-amber/10 text-amber" : isTrial ? "bg-amber/10 text-amber" : "bg-surface-3 text-text-muted"
                }`}>
                  {isPro ? "Pro" : isTrial ? "Essai" : "Gratuit"}
                </span>
                {isPro && <span className="text-sm text-text-muted">9 $/mois</span>}
                {isTrial && billing?.trial_started_at && (
                  <span className="text-sm text-text-muted">
                    Démarré le {new Date(billing.trial_started_at).toLocaleDateString()}
                  </span>
                )}
              </div>
              {billing?.plan_expires_at && (
                <p className="mt-2 text-sm text-amber">
                  Expire le : {new Date(billing.plan_expires_at).toLocaleDateString()}
                </p>
              )}
              <div className="mt-6">
                {isPro || isTrial ? (
                  <button onClick={handleManage} disabled={actionLoading} className="rounded border border-border px-4 py-2 text-sm font-medium text-text-secondary hover:border-border-hover hover:text-text-primary disabled:opacity-50 transition-colors">
                    {actionLoading ? "Chargement..." : "Gérer l'abonnement"}
                  </button>
                ) : (
                  <button onClick={handleUpgrade} disabled={actionLoading} className="rounded bg-amber px-6 py-2.5 text-sm font-medium text-surface-0 hover:bg-amber-bright disabled:opacity-50 transition-colors">
                    {actionLoading ? "Chargement..." : "Passer à Pro — 9 $/mois"}
                  </button>
                )}
              </div>
            </div>

            {/* Usage */}
            {stats && (
              <div className="rounded border border-border bg-surface-1 p-6">
                <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-text-muted">Utilisation ce mois-ci</h2>
                <div className="grid grid-cols-2 gap-6">
                  {[
                    { label: "Offres évaluées", value: stats.total_jobs },
                    { label: "Candidatures", value: stats.applied },
                    { label: "Coût IA", value: `$${stats.monthly_cost_usd.toFixed(2)}` },
                    { label: "Budget restant", value: `$${stats.budget_remaining_usd.toFixed(2)}` },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="font-mono text-2xl font-bold text-text-primary">{item.value}</div>
                      <div className="text-sm text-text-muted">{item.label}</div>
                    </div>
                  ))}
                </div>
                {/* Budget bar */}
                {stats.monthly_cost_usd > 0 && (
                  <div className="mt-4">
                    <div className="h-2 overflow-hidden rounded-full bg-surface-3">
                      <div
                        className={`h-full rounded-full transition-all ${stats.budget_remaining_usd < 1 ? "bg-negative" : "bg-amber"}`}
                        style={{ width: `${Math.min(100, (stats.monthly_cost_usd / (stats.monthly_cost_usd + stats.budget_remaining_usd)) * 100)}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Plan comparison */}
            {!isPro && (
              <div className="rounded border border-border bg-surface-1 p-6">
                <h2 className="mb-4 text-lg font-semibold">Pourquoi passer à Pro ?</h2>
                <ul className="space-y-2 text-sm text-text-secondary">
                  {[
                    "Évaluation illimitée des offres (vs 10/cycle en Gratuit)",
                    "Notifications Telegram instantanées",
                    "Candidature automatique (CV + lettre de motivation)",
                    "Recherche entreprise IA",
                    "Support prioritaire",
                  ].map((f) => (
                    <li key={f} className="flex items-center gap-2">
                      <CheckIcon size={14} className="text-positive" /> {f}
                    </li>
                  ))}
                </ul>
                <button onClick={handleUpgrade} disabled={actionLoading} className="mt-6 rounded bg-amber px-6 py-2.5 text-sm font-medium text-surface-0 hover:bg-amber-bright disabled:opacity-50 transition-colors">
                  {actionLoading ? "Chargement..." : "Passer à Pro — 9 $/mois"}
                </button>
              </div>
            )}
          </div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
