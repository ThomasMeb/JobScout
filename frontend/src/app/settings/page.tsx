"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import AppShell from "@/components/AppShell";
import ProfileForm from "@/components/ProfileForm";
import { deleteAccount, getProfile, updateProfile } from "@/lib/api";
import { createClient } from "@/lib/supabase-browser";
import type { Profile } from "@/lib/types";
import { CheckIcon, BellIcon } from "@/components/Icons";

export default function SettingsPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function handleSubmit(data: Partial<Profile>) {
    await updateProfile(data as Record<string, unknown>);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  async function handleDeleteAccount() {
    setDeleting(true);
    try {
      await deleteAccount();
      const supabase = createClient();
      await supabase.auth.signOut();
      router.push("/");
    } catch (e) {
      console.error("Failed to delete account:", e);
      setDeleting(false);
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

  return (
    <AuthGuard>
      <AppShell>
        <div className="px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl space-y-6">
            <div>
              <h1 className="font-display text-3xl italic text-text-primary" style={{ letterSpacing: "-0.02em" }}>Paramètres</h1>
              <p className="mt-1 text-sm text-text-secondary">Gérez votre profil et vos préférences.</p>
            </div>

            {saved && (
              <div className="flex items-center gap-2 rounded border border-positive/30 bg-positive/5 p-3 text-sm text-positive">
                <CheckIcon size={16} /> Paramètres enregistrés avec succès !
              </div>
            )}

            {profile && <ProfileForm profile={profile} onSubmit={handleSubmit} mode="settings" />}

            {/* Telegram Setup Guide */}
            <div className="rounded border border-border bg-surface-1 p-6">
              <div className="flex items-center gap-2 mb-3">
                <BellIcon size={18} className="text-amber" />
                <h2 className="text-lg font-semibold">Notifications Telegram</h2>
              </div>
              <p className="mb-4 text-sm text-text-secondary">
                Recevez des notifications instantanées pour les offres les mieux notées.
              </p>
              <ol className="list-inside list-decimal space-y-2 text-sm text-text-secondary">
                <li>Ouvrez Telegram et cherchez <strong className="text-text-primary">@JobScoutNotifBot</strong></li>
                <li>Envoyez <code className="rounded bg-surface-3 px-1.5 py-0.5 font-mono text-xs text-amber">/start</code> au bot</li>
                <li>Le bot vous fournira votre Chat ID — collez-le ci-dessus</li>
              </ol>
              {profile?.telegram_chat_id ? (
                <div className="mt-4 flex items-center gap-2 text-sm text-positive">
                  <CheckIcon size={14} />
                  Telegram connecté (Chat ID : <span className="font-mono">{profile.telegram_chat_id}</span>)
                </div>
              ) : (
                <div className="mt-4 text-sm text-amber">Telegram pas encore connecté.</div>
              )}
            </div>

            {/* Danger Zone */}
            <div className="rounded border border-negative/30 bg-surface-1 p-6">
              <h2 className="mb-3 text-lg font-semibold text-negative">Zone de danger</h2>
              {!deleteConfirm ? (
                <button onClick={() => setDeleteConfirm(true)} className="rounded border border-negative/30 px-4 py-2 text-sm text-negative hover:bg-negative/5 transition-colors">
                  Supprimer mon compte
                </button>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-negative">
                    Cela supprimera définitivement votre compte et toutes vos données. Cette action est irréversible.
                  </p>
                  <div className="flex gap-3">
                    <button onClick={handleDeleteAccount} disabled={deleting} className="rounded bg-negative px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50 transition">
                      {deleting ? "Suppression..." : "Oui, supprimer mon compte"}
                    </button>
                    <button onClick={() => setDeleteConfirm(false)} className="rounded border border-border px-4 py-2 text-sm text-text-secondary hover:border-border-hover transition-colors">
                      Annuler
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
