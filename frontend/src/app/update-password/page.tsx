"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import AuthLayout from "@/components/AuthLayout";
import { LockIcon } from "@/components/Icons";
import { createClient } from "@/lib/supabase-browser";
import { translateAuthError } from "@/lib/auth-errors";

export default function UpdatePasswordPage() {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const router = useRouter();
  const supabase = createClient();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage("");
    if (password !== confirm) {
      setMessage("Les mots de passe ne correspondent pas.");
      return;
    }
    setLoading(true);
    const { error } = await supabase.auth.updateUser({ password });
    if (error) {
      setMessage(translateAuthError(error.message));
    } else {
      setMessage("Mot de passe mis à jour avec succès !");
      setTimeout(() => router.push("/dashboard"), 1500);
    }
    setLoading(false);
  }

  const inputClass =
    "w-full rounded border border-border bg-surface-1 py-2.5 pl-10 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:border-amber focus:outline-none focus:ring-1 focus:ring-amber transition-colors";

  return (
    <AuthLayout tagline="Sécurisez votre compte avec un nouveau mot de passe.">
      <div className="text-center">
        <h1 className="text-xl font-bold text-text-primary">Nouveau mot de passe</h1>
        <p className="mt-1 text-sm text-text-secondary">Définissez votre nouveau mot de passe</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <LockIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Nouveau mot de passe (min. 6 caractères)" required minLength={6} className={inputClass} />
        </div>
        <div className="relative">
          <LockIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Confirmer le nouveau mot de passe" required minLength={6} className={inputClass} />
        </div>
        <button type="submit" disabled={loading} className="w-full rounded bg-amber py-2.5 text-sm font-medium text-surface-0 hover:bg-amber-bright disabled:opacity-50 transition-colors">
          {loading ? "Mise à jour..." : "Mettre à jour le mot de passe"}
        </button>
      </form>

      {message && (
        <p className={`text-center text-sm ${message.includes("succès") ? "text-positive" : "text-negative"}`}>
          {message}
        </p>
      )}
    </AuthLayout>
  );
}
