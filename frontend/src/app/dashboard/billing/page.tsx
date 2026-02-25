"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AuthGuard from "@/components/AuthGuard";
import { createCheckout, createPortal, getBillingStatus, getProfile, getStats } from "@/lib/api";
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
      .then(([b, s, p]) => {
        setBilling(b);
        setStats(s);
        setProfilePlan(p.plan || "free");
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function handleUpgrade() {
    setActionLoading(true);
    try {
      const { checkout_url } = await createCheckout();
      if (checkout_url) window.location.href = checkout_url;
    } catch (e) {
      console.error("Checkout failed:", e);
    }
    setActionLoading(false);
  }

  async function handleManage() {
    setActionLoading(true);
    try {
      const { portal_url } = await createPortal();
      if (portal_url) window.location.href = portal_url;
    } catch (e) {
      console.error("Portal failed:", e);
    }
    setActionLoading(false);
  }

  const isPro = profilePlan === "pro";
  const isTrial = profilePlan === "trial";

  if (loading) {
    return (
      <AuthGuard>
        <div className="flex min-h-screen items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <nav className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
          <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-3">
            <div className="flex items-center gap-4">
              <Link href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400">
                &larr; Dashboard
              </Link>
              <h1 className="text-lg font-bold">Billing</h1>
            </div>
            <Link
              href="/settings"
              className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
            >
              Settings
            </Link>
          </div>
        </nav>

        <div className="mx-auto max-w-2xl space-y-8 px-6 py-8">
          {/* Current Plan */}
          <div className="rounded-xl border border-gray-200 p-6 dark:border-gray-800">
            <h2 className="mb-1 text-lg font-semibold">Current plan</h2>
            <div className="flex items-center gap-3">
              <span className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${
                isPro
                  ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
                  : isTrial
                    ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
                    : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
              }`}>
                {isPro ? "Pro" : isTrial ? "Trial" : "Free"}
              </span>
              {isPro && <span className="text-sm text-gray-500">$9/month</span>}
              {isTrial && billing?.trial_started_at && (
                <span className="text-sm text-gray-500">
                  Trial started {new Date(billing.trial_started_at).toLocaleDateString()}
                </span>
              )}
            </div>

            {billing?.plan_expires_at && (
              <p className="mt-2 text-sm text-yellow-600">
                Expires: {new Date(billing.plan_expires_at).toLocaleDateString()}
              </p>
            )}

            <div className="mt-6">
              {isPro || isTrial ? (
                <button
                  onClick={handleManage}
                  disabled={actionLoading}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:hover:bg-gray-900"
                >
                  {actionLoading ? "Loading..." : "Manage subscription"}
                </button>
              ) : (
                <button
                  onClick={handleUpgrade}
                  disabled={actionLoading}
                  className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {actionLoading ? "Loading..." : "Upgrade to Pro — $9/month"}
                </button>
              )}
            </div>
          </div>

          {/* Usage */}
          {stats && (
            <div className="rounded-xl border border-gray-200 p-6 dark:border-gray-800">
              <h2 className="mb-4 text-lg font-semibold">Usage this month</h2>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <div className="text-2xl font-bold">{stats.total_jobs}</div>
                  <div className="text-sm text-gray-500">Jobs scored</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">{stats.applied}</div>
                  <div className="text-sm text-gray-500">Applications</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">${stats.monthly_cost_usd.toFixed(2)}</div>
                  <div className="text-sm text-gray-500">AI cost</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">${stats.budget_remaining_usd.toFixed(2)}</div>
                  <div className="text-sm text-gray-500">Budget remaining</div>
                </div>
              </div>
            </div>
          )}

          {/* Plan comparison */}
          {!isPro && (
            <div className="rounded-xl border border-gray-200 p-6 dark:border-gray-800">
              <h2 className="mb-4 text-lg font-semibold">Why upgrade to Pro?</h2>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li className="flex items-center gap-2">
                  <span className="text-green-600">&#10003;</span> Unlimited job scoring (vs 10/cycle on Free)
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-600">&#10003;</span> Telegram instant notifications
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-600">&#10003;</span> Auto-apply pipeline (CV + cover letter)
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-600">&#10003;</span> Company research AI
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-600">&#10003;</span> Priority support
                </li>
              </ul>
              <button
                onClick={handleUpgrade}
                disabled={actionLoading}
                className="mt-6 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {actionLoading ? "Loading..." : "Upgrade to Pro — $9/month"}
              </button>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
