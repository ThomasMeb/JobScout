"use client";

import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import ProfileForm from "@/components/ProfileForm";
import { updateProfile } from "@/lib/api";
import type { Profile } from "@/lib/types";

export default function OnboardingPage() {
  const router = useRouter();

  async function handleSubmit(data: Partial<Profile>) {
    await updateProfile(data as Record<string, unknown>);
    router.push("/dashboard");
  }

  return (
    <AuthGuard>
      <div className="flex min-h-screen items-center justify-center px-4 py-12">
        <div className="w-full max-w-lg">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-bold">Bienvenue sur JobScout</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Configurons votre profil pour trouver les meilleures offres pour vous.
            </p>
          </div>
          <ProfileForm profile={{}} onSubmit={handleSubmit} mode="onboarding" />
        </div>
      </div>
    </AuthGuard>
  );
}
