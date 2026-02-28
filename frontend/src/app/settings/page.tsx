"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AuthGuard from "@/components/AuthGuard";
import ProfileForm from "@/components/ProfileForm";
import { deleteAccount, getProfile, updateProfile } from "@/lib/api";
import { createClient } from "@/lib/supabase-browser";
import type { Profile } from "@/lib/types";

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

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
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
                &larr; Tableau de bord
              </Link>
              <h1 className="text-lg font-bold">Paramètres</h1>
            </div>
            <button
              onClick={handleLogout}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Se déconnecter
            </button>
          </div>
        </nav>

        <div className="mx-auto max-w-2xl space-y-8 px-6 py-8">
          {saved && (
            <div className="rounded-lg bg-green-50 p-3 text-center text-sm text-green-700 dark:bg-green-900/20 dark:text-green-300">
              Paramètres enregistrés avec succès !
            </div>
          )}

          {/* Profile & Job Preferences */}
          {profile && (
            <ProfileForm profile={profile} onSubmit={handleSubmit} mode="settings" />
          )}

          {/* Telegram Setup Guide */}
          <div className="rounded-xl border border-gray-200 p-6 dark:border-gray-800">
            <h2 className="mb-3 text-lg font-semibold">Notifications Telegram</h2>
            <p className="mb-4 text-sm text-gray-600 dark:text-gray-400">
              Recevez des notifications instantanées pour les offres les mieux notées sur Telegram.
            </p>
            <ol className="list-inside list-decimal space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li>
                Ouvrez Telegram et cherchez <strong>@JobScoutNotifBot</strong>
              </li>
              <li>
                Envoyez <code>/start</code> au bot
              </li>
              <li>
                Le bot vous fournira votre Chat ID — collez-le dans le champ Telegram Chat ID ci-dessus
              </li>
            </ol>
            {profile?.telegram_chat_id ? (
              <div className="mt-4 flex items-center gap-2 text-sm text-green-600">
                <span>&#10003;</span>
                <span>Telegram connecté (Chat ID : {profile.telegram_chat_id})</span>
              </div>
            ) : (
              <div className="mt-4 text-sm text-yellow-600 dark:text-yellow-400">
                Telegram pas encore connecté.
              </div>
            )}
          </div>

          {/* Danger Zone */}
          <div className="rounded-xl border border-red-200 p-6 dark:border-red-900">
            <h2 className="mb-3 text-lg font-semibold text-red-600">Zone de danger</h2>

            {!deleteConfirm ? (
              <button
                onClick={() => setDeleteConfirm(true)}
                className="rounded-lg border border-red-300 px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-950"
              >
                Supprimer mon compte
              </button>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-red-600">
                  Cela supprimera définitivement votre compte et toutes vos données (profil, offres, candidatures).
                  Cette action est irréversible.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={handleDeleteAccount}
                    disabled={deleting}
                    className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                  >
                    {deleting ? "Suppression..." : "Oui, supprimer mon compte"}
                  </button>
                  <button
                    onClick={() => setDeleteConfirm(false)}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-900"
                  >
                    Annuler
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
