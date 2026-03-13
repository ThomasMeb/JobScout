"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Logo from "@/components/Logo";
import { createClient } from "@/lib/supabase-browser";
import { translateAuthError } from "@/lib/auth-errors";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"signin" | "signup" | "magic">("signin");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const router = useRouter();
  const supabase = createClient();

  async function handlePasswordLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      setMessage(translateAuthError(error.message));
    } else {
      router.push("/dashboard");
    }
    setLoading(false);
  }

  async function handleSignUp(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });

    if (error) {
      setMessage(translateAuthError(error.message));
    } else {
      setMessage("Vérifiez votre email pour confirmer votre compte !");
    }
    setLoading(false);
  }

  async function handleMagicLink(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });

    if (error) {
      setMessage(translateAuthError(error.message));
    } else {
      setMessage("Vérifiez votre email pour le lien de connexion !");
    }
    setLoading(false);
  }

  async function handleOAuth(provider: "google" | "github") {
    await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <Link href="/"><Logo size="lg" /></Link>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            {mode === "signup" ? "Créez votre compte" : "Connectez-vous à votre compte"}
          </p>
        </div>

        {/* OAuth */}
        <div className="space-y-3">
          <button
            onClick={() => handleOAuth("google")}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800"
          >
            Continuer avec Google
          </button>
          <button
            onClick={() => handleOAuth("github")}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800"
          >
            Continuer avec GitHub
          </button>
        </div>

        <div className="flex items-center gap-4">
          <div className="h-px flex-1 bg-gray-200 dark:bg-gray-700" />
          <span className="text-xs text-gray-500">OU</span>
          <div className="h-px flex-1 bg-gray-200 dark:bg-gray-700" />
        </div>

        {/* Sign in with password */}
        {mode === "signin" && (
          <form onSubmit={handlePasswordLogin} className="space-y-3">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm dark:border-gray-600 dark:bg-gray-800"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mot de passe"
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm dark:border-gray-600 dark:bg-gray-800"
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Connexion..." : "Se connecter"}
            </button>
            <div className="flex justify-between text-xs text-gray-500">
              <button type="button" onClick={() => setMode("magic")} className="hover:text-gray-700 dark:hover:text-gray-300">
                Utiliser un lien magique
              </button>
              <Link href="/forgot-password" className="hover:text-gray-700 dark:hover:text-gray-300">
                Mot de passe oublié ?
              </Link>
            </div>
          </form>
        )}

        {/* Sign up */}
        {mode === "signup" && (
          <form onSubmit={handleSignUp} className="space-y-3">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm dark:border-gray-600 dark:bg-gray-800"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mot de passe (min. 6 caractères)"
              required
              minLength={6}
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm dark:border-gray-600 dark:bg-gray-800"
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Création du compte..." : "Créer un compte"}
            </button>
            <button
              type="button"
              onClick={() => setMode("magic")}
              className="w-full text-center text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              Utiliser un lien magique
            </button>
          </form>
        )}

        {/* Magic link */}
        {mode === "magic" && (
          <form onSubmit={handleMagicLink} className="space-y-3">
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
              {loading ? "Envoi en cours..." : "Envoyer le lien magique"}
            </button>
            <button
              type="button"
              onClick={() => setMode("signin")}
              className="w-full text-center text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              Utiliser un mot de passe
            </button>
          </form>
        )}

        {message && (
          <p className={`text-center text-sm ${message.includes("Vérifiez") ? "text-green-600" : "text-red-600"}`}>
            {message}
          </p>
        )}

        {/* Toggle sign in / sign up */}
        <p className="text-center text-sm text-gray-500">
          {mode === "signup" ? (
            <>
              Vous avez déjà un compte ?{" "}
              <button onClick={() => setMode("signin")} className="text-blue-600 hover:underline">
                Se connecter
              </button>
            </>
          ) : (
            <>
              Vous n&apos;avez pas de compte ?{" "}
              <button onClick={() => setMode("signup")} className="text-blue-600 hover:underline">
                S&apos;inscrire
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
