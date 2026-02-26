import Link from "next/link";
import Logo from "@/components/Logo";

export default function LegalLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-white dark:bg-gray-950">
      <header className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/"><Logo size="md" /></Link>
          <Link
            href="/login"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Get started
          </Link>
        </div>
      </header>
      <main className="flex-1 px-6 py-12">
        <div className="prose prose-gray dark:prose-invert mx-auto max-w-3xl">
          {children}
        </div>
      </main>
      <footer className="border-t border-gray-200 px-6 py-8 dark:border-gray-800">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <div className="text-sm text-gray-500">&copy; {new Date().getFullYear()} JobScout</div>
          <nav className="flex gap-6 text-sm text-gray-500">
            <Link href="/legal/privacy" className="hover:text-gray-900 dark:hover:text-white">Privacy</Link>
            <Link href="/legal/terms" className="hover:text-gray-900 dark:hover:text-white">Terms</Link>
            <Link href="/legal/mentions" className="hover:text-gray-900 dark:hover:text-white">Legal</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
