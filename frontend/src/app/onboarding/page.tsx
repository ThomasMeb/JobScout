"use client";

import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import ProfileForm from "@/components/ProfileForm";
import Logo from "@/components/Logo";
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
      <div className="relative min-h-screen bg-gradient-to-b from-surface-0 to-surface-1">
        <div className="hero-grid absolute inset-0 opacity-20" />
        <div className="relative flex min-h-screen items-center justify-center px-4 py-12">
          <div className="w-full max-w-lg">
            <div className="mb-8 text-center">
              <Logo size="lg" className="justify-center" />
              <h1 className="mt-4 text-2xl font-bold tracking-tight" style={{ letterSpacing: "-0.03em" }}>
                Bienvenue sur JobScout
              </h1>
              <p className="mt-2 text-text-secondary">
                Configurons votre profil pour trouver les meilleures offres pour vous.
              </p>
            </div>
            <ProfileForm profile={{}} onSubmit={handleSubmit} mode="onboarding" />
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
