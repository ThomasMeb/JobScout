"use client";

import { useState } from "react";
import Link from "next/link";
import Logo from "@/components/Logo";
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
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <Link href="/"><Logo size="lg" /></Link>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Réinitialiser votre mot de passe</p>
        </div>

        {sent ? (
          <div className="text-center">
            <p className="text-green-600">Vérifiez votre email pour le lien de réinitialisation !</p>
            <Link href="/login" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
              Retour à la connexion
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Entrez votre adresse email et nous vous enverrons un lien pour réinitialiser votre mot de passe.
            </p>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm dark:border-gray-600 dark:bg-gray-800"
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Envoi en cours..." : "Envoyer le lien de réinitialisation"}
            </button>
            {error && <p className="text-center text-sm text-red-600">{error}</p>}
            <Link
              href="/login"
              className="block text-center text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              Retour à la connexion
            </Link>
          </form>
        )}
      </div>
    </div>
  );
}
