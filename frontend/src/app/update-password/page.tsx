"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase-browser";

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
      setMessage("Passwords do not match.");
      return;
    }

    setLoading(true);

    const { error } = await supabase.auth.updateUser({ password });

    if (error) {
      setMessage(error.message);
    } else {
      setMessage("Password updated successfully!");
      setTimeout(() => router.push("/dashboard"), 1500);
    }
    setLoading(false);
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <Link href="/" className="text-2xl font-bold">
            <span className="text-blue-600">Job</span>Scout
          </Link>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Set your new password</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="New password (min 6 characters)"
            required
            minLength={6}
            className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm dark:border-gray-600 dark:bg-gray-800"
          />
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Confirm new password"
            required
            minLength={6}
            className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm dark:border-gray-600 dark:bg-gray-800"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Updating..." : "Update password"}
          </button>
        </form>

        {message && (
          <p className={`text-center text-sm ${message.includes("success") ? "text-green-600" : "text-red-600"}`}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
}
