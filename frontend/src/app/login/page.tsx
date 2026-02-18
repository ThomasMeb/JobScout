"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase-browser";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const supabase = createClient();

  async function handleMagicLink(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/dashboard` },
    });

    if (error) {
      setMessage(error.message);
    } else {
      setMessage("Check your email for the login link!");
    }
    setLoading(false);
  }

  async function handleOAuth(provider: "google" | "github") {
    await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: `${window.location.origin}/dashboard` },
    });
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold">
            <span className="text-blue-600">Job</span>Scout
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Sign in to your account</p>
        </div>

        {/* OAuth */}
        <div className="space-y-3">
          <button
            onClick={() => handleOAuth("google")}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800"
          >
            Continue with Google
          </button>
          <button
            onClick={() => handleOAuth("github")}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800"
          >
            Continue with GitHub
          </button>
        </div>

        <div className="flex items-center gap-4">
          <div className="h-px flex-1 bg-gray-200 dark:bg-gray-700" />
          <span className="text-xs text-gray-500">OR</span>
          <div className="h-px flex-1 bg-gray-200 dark:bg-gray-700" />
        </div>

        {/* Magic link */}
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
            {loading ? "Sending..." : "Send magic link"}
          </button>
        </form>

        {message && (
          <p className={`text-center text-sm ${message.includes("Check") ? "text-green-600" : "text-red-600"}`}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
}
