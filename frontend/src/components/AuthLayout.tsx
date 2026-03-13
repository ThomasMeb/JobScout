import Link from "next/link";
import Logo from "@/components/Logo";

export default function AuthLayout({
  children,
  tagline = "Votre prochain poste, trouvé par l'IA.",
}: {
  children: React.ReactNode;
  tagline?: string;
}) {
  return (
    <div className="flex min-h-screen bg-surface-0">
      {/* Left decorative panel — desktop only */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-surface-2 to-surface-1 items-center justify-center">
        {/* Grid pattern */}
        <div className="hero-grid absolute inset-0 opacity-30" />
        {/* Amber glow */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full bg-amber/8 blur-3xl" />

        <div className="relative z-10 max-w-md px-12 text-center">
          <Logo size="lg" />
          <p className="mt-6 text-lg text-text-secondary leading-relaxed">
            {tagline}
          </p>
          <div className="mt-8 flex justify-center gap-8 text-text-muted">
            <div className="text-center">
              <div className="font-mono text-2xl font-bold text-amber-bright">10+</div>
              <div className="mt-1 text-xs uppercase tracking-wider">Sources</div>
            </div>
            <div className="text-center">
              <div className="font-mono text-2xl font-bold text-amber-bright">IA</div>
              <div className="mt-1 text-xs uppercase tracking-wider">Scoring</div>
            </div>
            <div className="text-center">
              <div className="font-mono text-2xl font-bold text-amber-bright">Auto</div>
              <div className="mt-1 text-xs uppercase tracking-wider">Candidature</div>
            </div>
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex w-full items-center justify-center px-6 lg:w-1/2">
        <div className="w-full max-w-sm space-y-6">
          {/* Mobile logo */}
          <div className="text-center lg:hidden">
            <Link href="/"><Logo size="lg" /></Link>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
