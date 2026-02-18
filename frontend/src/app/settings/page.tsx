"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import ProfileForm from "@/components/ProfileForm";
import { getProfile, updateProfile } from "@/lib/api";
import { createClient } from "@/lib/supabase-browser";
import type { Profile } from "@/lib/types";

export default function SettingsPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);

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
              <a href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400">
                &larr; Dashboard
              </a>
              <h1 className="text-lg font-bold">Settings</h1>
            </div>
            <button
              onClick={handleLogout}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Sign out
            </button>
          </div>
        </nav>

        <div className="mx-auto max-w-2xl px-6 py-8">
          {saved && (
            <div className="mb-6 rounded-lg bg-green-50 p-3 text-center text-sm text-green-700 dark:bg-green-900/20 dark:text-green-300">
              Settings saved successfully!
            </div>
          )}

          {profile && (
            <ProfileForm profile={profile} onSubmit={handleSubmit} mode="settings" />
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
