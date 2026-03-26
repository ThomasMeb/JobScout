"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";
import AuthGuard from "@/components/AuthGuard";
import ProfileForm from "@/components/ProfileForm";
import Logo from "@/components/Logo";
import { updateProfile } from "@/lib/api";
import { createClient } from "@/lib/supabase-browser";
import type { Profile } from "@/lib/types";

export default function OnboardingPage() {
  const router = useRouter();

  async function handleSubmit(data: Partial<Profile>) {
    try {
      await updateProfile(data as Record<string, unknown>);
      toast.success("Profil configuré !");
      router.push("/dashboard");
    } catch {
      toast.error("Erreur lors de la sauvegarde. Réessayez.");
    }
  }

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  }

  return (
    <AuthGuard>
      <div className="relative min-h-screen bg-gradient-to-b from-surface-0 to-surface-1">
        <div className="hero-grid absolute inset-0 opacity-20" />
        <div className="relative flex min-h-screen items-center justify-center px-4 py-12">
          <div className="w-full max-w-lg">
            <div className="mb-8 text-center">
              <Logo size="lg" className="justify-center" />
              <h1 className="mt-4 font-display text-3xl italic text-text-primary" style={{ letterSpacing: "-0.02em" }}>
                Bienvenue sur JobScout
              </h1>
              <p className="mt-2 text-text-secondary">
                Configurons votre profil pour trouver les meilleures offres pour vous.
              </p>
            </div>
            <ProfileForm profile={{}} onSubmit={handleSubmit} mode="onboarding" />
            <div className="mt-6 text-center">
              <button onClick={handleLogout} className="text-sm text-text-muted hover:text-text-secondary transition-colors">
                Se déconnecter
              </button>
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
