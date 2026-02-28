"use client";

import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-2xl font-bold">
          <span className="text-blue-600">Job</span>
          <span className="text-gray-900 dark:text-white">Scout</span>
        </h1>

        <p className="mt-6 text-6xl font-bold text-gray-900 dark:text-white">404</p>
        <p className="mt-2 text-lg text-gray-600 dark:text-gray-400">
          Page introuvable
        </p>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-500">
          La page que vous recherchez n&apos;existe pas ou a été déplacée.
        </p>

        <div className="mt-8 flex flex-col items-center gap-3">
          <Link
            href="/dashboard"
            className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            Retour au tableau de bord
          </Link>
          <Link
            href="/"
            className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          >
            Retour à l&apos;accueil
          </Link>
        </div>
      </div>
    </div>
  );
}
