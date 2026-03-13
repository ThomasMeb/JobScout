"use client";

import Link from "next/link";
import Logo from "@/components/Logo";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-0 px-4">
      <div className="text-center">
        <Logo size="md" className="justify-center" />

        <p className="mt-8 font-mono text-7xl font-bold text-amber">404</p>
        <p className="mt-2 text-lg text-text-primary">Page introuvable</p>
        <p className="mt-1 text-sm text-text-muted">
          La page que vous recherchez n&apos;existe pas ou a été déplacée.
        </p>

        <div className="mt-8 flex flex-col items-center gap-3">
          <Link href="/dashboard" className="rounded bg-amber px-6 py-2.5 text-sm font-medium text-surface-0 hover:bg-amber-bright transition-colors">
            Retour au tableau de bord
          </Link>
          <Link href="/" className="text-sm text-text-muted hover:text-text-primary transition-colors">
            Retour à l&apos;accueil
          </Link>
        </div>
      </div>
    </div>
  );
}
