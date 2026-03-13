"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AuthLayout from "@/components/AuthLayout";
import { GoogleIcon, GitHubIcon, MailIcon, LockIcon } from "@/components/Icons";
import { createClient } from "@/lib/supabase-browser";
import { translateAuthError } from "@/lib/auth-errors";
import { isMockMode } from "@/lib/mock-data";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"signin" | "signup" | "magic">("signin");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const router = useRouter();
  const supabase = createClient();

  // Mock mode: go straight to dashboard
  useEffect(() => {
    if (isMockMode()) router.push("/dashboard");
  }, [router]);

  async function handlePasswordLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    const { error } = await supabase.auth.signInWithPassword({ email, password });
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
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
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

  const inputClass =
    "w-full rounded border border-border bg-surface-1 py-2.5 pl-10 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:border-amber focus:outline-none focus:ring-1 focus:ring-amber transition-colors";

  return (
    <AuthLayout>
      <div className="text-center">
        <h1 className="text-xl font-bold text-text-primary">
          {mode === "signup" ? "Créez votre compte" : "Connectez-vous"}
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          {mode === "signup"
            ? "Commencez à trouver vos matchs emploi"
            : "Accédez à votre tableau de bord"}
        </p>
      </div>

      {/* OAuth */}
      <div className="space-y-3">
        <button
          onClick={() => handleOAuth("google")}
          className="flex w-full items-center justify-center gap-3 rounded border border-border bg-surface-1 px-4 py-2.5 text-sm font-medium text-text-primary hover:border-border-hover hover:bg-surface-2 transition-colors"
        >
          <GoogleIcon />
          Continuer avec Google
        </button>
        <button
          onClick={() => handleOAuth("github")}
          className="flex w-full items-center justify-center gap-3 rounded border border-border bg-surface-1 px-4 py-2.5 text-sm font-medium text-text-primary hover:border-border-hover hover:bg-surface-2 transition-colors"
        >
          <GitHubIcon />
          Continuer avec GitHub
        </button>
      </div>

      <div className="flex items-center gap-4">
        <div className="h-px flex-1 bg-border" />
        <span className="text-xs font-medium uppercase tracking-wider text-text-muted">ou</span>
        <div className="h-px flex-1 bg-border" />
      </div>

      {/* Sign in with password */}
      {mode === "signin" && (
        <form onSubmit={handlePasswordLogin} className="space-y-3">
          <div className="relative">
            <MailIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required className={inputClass} />
          </div>
          <div className="relative">
            <LockIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mot de passe" required className={inputClass} />
          </div>
          <button type="submit" disabled={loading} className="w-full rounded bg-amber py-2.5 text-sm font-medium text-surface-0 hover:bg-amber-bright disabled:opacity-50 transition-colors">
            {loading ? "Connexion..." : "Se connecter"}
          </button>
          <div className="flex justify-between text-xs text-text-muted">
            <button type="button" onClick={() => setMode("magic")} className="hover:text-text-secondary transition-colors">Utiliser un lien magique</button>
            <Link href="/forgot-password" className="hover:text-text-secondary transition-colors">Mot de passe oublié ?</Link>
          </div>
        </form>
      )}

      {/* Sign up */}
      {mode === "signup" && (
        <form onSubmit={handleSignUp} className="space-y-3">
          <div className="relative">
            <MailIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required className={inputClass} />
          </div>
          <div className="relative">
            <LockIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mot de passe (min. 6 caractères)" required minLength={6} className={inputClass} />
          </div>
          <button type="submit" disabled={loading} className="w-full rounded bg-amber py-2.5 text-sm font-medium text-surface-0 hover:bg-amber-bright disabled:opacity-50 transition-colors">
            {loading ? "Création du compte..." : "Créer un compte"}
          </button>
          <button type="button" onClick={() => setMode("magic")} className="w-full text-center text-xs text-text-muted hover:text-text-secondary transition-colors">
            Utiliser un lien magique
          </button>
        </form>
      )}

      {/* Magic link */}
      {mode === "magic" && (
        <form onSubmit={handleMagicLink} className="space-y-3">
          <div className="relative">
            <MailIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required className={inputClass} />
          </div>
          <button type="submit" disabled={loading} className="w-full rounded bg-amber py-2.5 text-sm font-medium text-surface-0 hover:bg-amber-bright disabled:opacity-50 transition-colors">
            {loading ? "Envoi en cours..." : "Envoyer le lien magique"}
          </button>
          <button type="button" onClick={() => setMode("signin")} className="w-full text-center text-xs text-text-muted hover:text-text-secondary transition-colors">
            Utiliser un mot de passe
          </button>
        </form>
      )}

      {message && (
        <p className={`text-center text-sm ${message.includes("Vérifiez") ? "text-positive" : "text-negative"}`}>
          {message}
        </p>
      )}

      <p className="text-center text-sm text-text-muted">
        {mode === "signup" ? (
          <>Vous avez déjà un compte ?{" "}<button onClick={() => setMode("signin")} className="text-amber hover:text-amber-bright transition-colors">Se connecter</button></>
        ) : (
          <>Vous n&apos;avez pas de compte ?{" "}<button onClick={() => setMode("signup")} className="text-amber hover:text-amber-bright transition-colors">S&apos;inscrire</button></>
        )}
      </p>
    </AuthLayout>
  );
}
