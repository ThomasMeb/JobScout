import Link from "next/link";
import Logo from "@/components/Logo";

export default function LegalLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-surface-0 text-text-primary">
      <header className="border-b border-border bg-surface-0">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/"><Logo size="md" /></Link>
          <Link href="/login" className="rounded bg-amber px-4 py-2 text-sm font-medium text-surface-0 hover:bg-amber-bright transition-colors">
            Commencer
          </Link>
        </div>
      </header>
      <main className="flex-1 px-6 py-12">
        <div className="prose prose-invert mx-auto max-w-3xl prose-headings:text-text-primary prose-p:text-text-secondary prose-li:text-text-secondary prose-strong:text-text-primary prose-a:text-amber">
          {children}
        </div>
      </main>
      <footer className="border-t border-border px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <div className="text-sm text-text-muted">&copy; {new Date().getFullYear()} JobScout</div>
          <nav className="flex gap-6 text-sm text-text-muted">
            <Link href="/legal/privacy" className="hover:text-text-primary transition-colors">Confidentialité</Link>
            <Link href="/legal/terms" className="hover:text-text-primary transition-colors">CGU</Link>
            <Link href="/legal/mentions" className="hover:text-text-primary transition-colors">Mentions légales</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
