"use client";

import { useState } from "react";
import Link from "next/link";
import AuthLayout from "@/components/AuthLayout";
import { MailIcon } from "@/components/Icons";
import { createClient } from "@/lib/supabase-browser";
import { translateAuthError } from "@/lib/auth-errors";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const supabase = createClient();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/callback?type=recovery`,
    });
    if (error) {
      setError(translateAuthError(error.message));
    } else {
      setSent(true);
    }
    setLoading(false);
  }

  return (
    <AuthLayout tagline="Réinitialisez votre mot de passe en quelques secondes.">
      <div className="text-center">
        <h1 className="text-xl font-bold text-text-primary">Mot de passe oublié</h1>
        <p className="mt-1 text-sm text-text-secondary">Réinitialiser votre mot de passe</p>
      </div>

      {sent ? (
        <div className="text-center space-y-4">
          <p className="text-sm text-positive">Vérifiez votre email pour le lien de réinitialisation !</p>
          <Link href="/login" className="inline-block text-sm text-amber hover:text-amber-bright transition-colors">
            Retour à la connexion
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          <p className="text-sm text-text-secondary">
            Entrez votre adresse email et nous vous enverrons un lien pour réinitialiser votre mot de passe.
          </p>
          <div className="relative">
            <MailIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full rounded border border-border bg-surface-1 py-2.5 pl-10 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:border-amber focus:outline-none focus:ring-1 focus:ring-amber transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded bg-amber py-2.5 text-sm font-medium text-surface-0 hover:bg-amber-bright disabled:opacity-50 transition-colors"
          >
            {loading ? "Envoi en cours..." : "Envoyer le lien de réinitialisation"}
          </button>
          {error && <p className="text-center text-sm text-negative">{error}</p>}
          <Link href="/login" className="block text-center text-xs text-text-muted hover:text-text-secondary transition-colors">
            Retour à la connexion
          </Link>
        </form>
      )}
    </AuthLayout>
  );
}
