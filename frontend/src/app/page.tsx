import type { Metadata } from "next";
import Link from "next/link";
import Logo from "@/components/Logo";
import JsonLd from "@/components/JsonLd";
import AnimatedSection from "@/components/AnimatedSection";
import { organizationJsonLd, softwareApplicationJsonLd } from "@/lib/structured-data";
import { SearchIcon, TargetIcon, ChartIcon, BellIcon, PenIcon, TrendingIcon, CheckIcon } from "@/components/Icons";
import ThemeToggle from "@/components/ThemeToggle";

export const metadata: Metadata = {
  title: "JobScout — Matching emploi par IA | Scraping & scoring automatique",
  description:
    "Scraping de 10+ sites d'emploi, scoring IA personnalisé de 0 à 100, candidature automatique. Trouvez votre prochain poste sans effort.",
  alternates: { canonical: "https://jobscout.mebarki.dev" },
};

const tickerItems = [
  { label: "WTTJ", score: 94, status: "▲" },
  { label: "RemoteOK", score: 87, status: "▲" },
  { label: "Adzuna", score: 73, status: "—" },
  { label: "France Travail", score: 81, status: "▲" },
  { label: "HelloWork", score: 68, status: "▼" },
  { label: "APEC", score: 76, status: "▲" },
  { label: "FreeWork", score: 91, status: "▲" },
  { label: "WeLoveDevs", score: 85, status: "▲" },
  { label: "Indeed", score: 72, status: "—" },
];

const features = [
  { icon: SearchIcon, title: "Scraping multi-sources", desc: "WTTJ, RemoteOK, Adzuna, France Travail, Indeed, LinkedIn — tout au même endroit.", accent: true },
  { icon: TargetIcon, title: "Scoring IA 0→100", desc: "Chaque offre évaluée par rapport à votre CV, compétences et attentes salariales." },
  { icon: ChartIcon, title: "Tableau de bord", desc: "Filtrez, triez et suivez vos candidatures avec des analyses en temps réel." },
  { icon: BellIcon, title: "Alertes Telegram", desc: "Notifications instantanées pour les offres à haut score." },
  { icon: PenIcon, title: "Candidature auto", desc: "CV adapté, lettre de motivation et email — tout généré en un clic." },
  { icon: TrendingIcon, title: "Veille entreprise", desc: "Taille, levées de fonds, stack technique, culture d'entreprise." },
];

const steps = [
  { num: "01", title: "Importez votre CV", desc: "Indiquez vos compétences et ce que vous recherchez. 5 minutes." },
  { num: "02", title: "L'IA trouve vos matchs", desc: "Scraping + scoring automatique toutes les quelques heures." },
  { num: "03", title: "Postulez en un clic", desc: "Candidature générée et envoyée directement." },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-surface-0 text-text-primary">
      <JsonLd data={organizationJsonLd()} />
      <JsonLd data={softwareApplicationJsonLd()} />

      {/* ─── Navbar ─── */}
      <header className="sticky top-0 z-50 border-b border-border bg-surface-0/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo size="md" />
          <nav className="flex items-center gap-4">
            <Link href="/pricing" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Tarifs
            </Link>
            <Link href="/login" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Se connecter
            </Link>
            <ThemeToggle />
            <Link
              href="/login"
              className="rounded bg-amber px-4 py-2 text-sm font-medium text-surface-0 hover:bg-amber-bright transition-colors"
            >
              Commencer gratuitement
            </Link>
          </nav>
        </div>
      </header>

      {/* ─── Hero — Asymmetric Editorial ─── */}
      <section className="relative overflow-hidden px-6 py-20 sm:py-28">
        {/* Background layers */}
        <div className="hero-grid absolute inset-0 opacity-30" />
        <div className="halftone absolute right-0 top-0 w-1/2 h-full" />
        <div className="absolute left-1/3 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full bg-amber/5 blur-3xl" />

        <div className="relative mx-auto max-w-6xl">
          <div className="grid gap-12 lg:grid-cols-[1fr,420px] lg:items-center">
            {/* Left — Editorial text */}
            <div>
              <div className="mb-6 inline-flex items-center gap-2 rounded border border-amber/20 bg-amber/5 px-4 py-1.5">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-amber" />
                </span>
                <span className="font-mono text-xs font-medium uppercase tracking-widest text-amber">Signal actif — 247 offres évaluées</span>
              </div>

              <h1 className="editorial-h1 mb-6 text-text-primary">
                Arrêtez de scroller.
                <br />
                <span className="text-amber-gradient">Trouvez votre signal.</span>
              </h1>

              <div className="editorial-divider mb-6 w-24" />

              <p className="mb-10 max-w-lg text-lg text-text-secondary leading-relaxed">
                JobScout scrape <span className="font-mono text-amber">10+</span> sites d&apos;emploi, évalue chaque offre
                par rapport à votre CV, et ne vous montre que les offres qui valent le coup.
              </p>

              <div className="flex flex-col gap-4 sm:flex-row">
                <Link
                  href="/login"
                  className="signal-glow rounded border border-amber bg-amber px-8 py-3.5 text-lg font-medium text-surface-0 hover:bg-amber-bright transition-colors"
                >
                  Essai gratuit — 14 jours
                </Link>
                <Link
                  href="/pricing"
                  className="rounded border border-border px-8 py-3.5 text-lg font-medium text-text-secondary hover:border-border-hover hover:text-text-primary transition-colors"
                >
                  Voir les tarifs
                </Link>
              </div>

              <p className="mt-4 text-sm text-text-muted">
                Sans carte bancaire &middot; Annulez à tout moment
              </p>
            </div>

            {/* Right — Floating Signal Card */}
            <AnimatedSection delay={0.3}>
              <div className="relative">
                {/* Decorative score */}
                <div className="absolute -top-8 -right-4 score-display score-display-high opacity-10 select-none pointer-events-none">
                  94
                </div>

                {/* Signal card */}
                <div className="signal-card p-5 shadow-2xl">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="label mb-1">Meilleur match du jour</div>
                      <h3 className="text-base font-semibold text-text-primary mb-0.5">Senior Data Scientist — NLP & LLM</h3>
                      <p className="text-sm text-text-secondary">Mistral AI · Paris · Hybrid</p>
                    </div>
                    <div className="flex flex-col items-center">
                      <div className="font-mono text-3xl font-bold text-positive">94</div>
                      <div className="text-[10px] uppercase tracking-wider text-text-muted">score</div>
                    </div>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {["Python", "NLP", "LLM", "PyTorch"].map((tag) => (
                      <span key={tag} className="tag-pill">{tag}</span>
                    ))}
                  </div>

                  <div className="mt-3 border-t border-border pt-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-text-muted">75k – 95k € · EUR</span>
                      <span className="flex items-center gap-1 text-positive">
                        <span className="h-1.5 w-1.5 rounded-full bg-positive" />
                        Match élevé
                      </span>
                    </div>
                  </div>
                </div>

                {/* Second card peeking */}
                <div className="signal-card mt-2 p-4 opacity-60">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-text-primary">Full-Stack Engineer (React + Python)</p>
                      <p className="text-xs text-text-secondary">Alan · Full Remote</p>
                    </div>
                    <div className="font-mono text-xl font-bold text-positive">91</div>
                  </div>
                </div>

                {/* Third card barely visible */}
                <div className="signal-card mt-2 p-3 opacity-30">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-text-secondary">MLOps Engineer — Datadog</p>
                    <div className="font-mono text-lg font-bold text-amber">85</div>
                  </div>
                </div>
              </div>
            </AnimatedSection>
          </div>
        </div>
      </section>

      {/* ─── Ticker Strip — Bloomberg-style ─── */}
      <section className="border-y border-border bg-surface-1 py-3 overflow-hidden">
        <div className="ticker-strip">
          <div className="ticker-strip-inner">
            {[...tickerItems, ...tickerItems].map((item, i) => (
              <span key={i} className="inline-flex items-center gap-3 px-6 text-sm">
                <span className="font-mono text-xs text-text-muted uppercase">{item.label}</span>
                <span className={`font-mono font-bold ${item.score >= 80 ? "text-positive" : item.score >= 60 ? "text-amber" : "text-negative"}`}>
                  {item.score}
                </span>
                <span className={`text-xs ${item.status === "▲" ? "text-positive" : item.status === "▼" ? "text-negative" : "text-text-muted"}`}>
                  {item.status}
                </span>
                <span className="text-border">│</span>
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Stats — Oversized Editorial Numbers ─── */}
      <section className="px-6 py-16">
        <div className="mx-auto max-w-5xl">
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
            {[
              { value: "10+", label: "Sources scrapées", sub: "en continu" },
              { value: "1k+", label: "Offres évaluées", sub: "par jour" },
              { value: "< 5$", label: "Coût mensuel", sub: "tout inclus" },
              { value: "5min", label: "Mise en place", sub: "c'est tout" },
            ].map((stat, i) => (
              <AnimatedSection key={stat.label} delay={i * 0.1}>
                <div className="text-center sm:text-left">
                  <div className="font-mono text-3xl font-bold text-amber-bright sm:text-4xl" style={{ letterSpacing: "-0.04em" }}>
                    {stat.value}
                  </div>
                  <div className="mt-1 text-sm font-medium text-text-primary">{stat.label}</div>
                  <div className="text-xs text-text-muted">{stat.sub}</div>
                </div>
              </AnimatedSection>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Features — Bento Grid ─── */}
      <section className="border-y border-border bg-surface-1 px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <AnimatedSection className="mb-12">
            <div className="flex items-end gap-4 mb-3">
              <span className="section-number">01</span>
              <div>
                <h2 className="text-3xl font-bold" style={{ letterSpacing: "-0.03em" }}>
                  Tout ce qu&apos;il faut
                </h2>
                <p className="text-text-secondary">Du scraping à la candidature — automatisé.</p>
              </div>
            </div>
            <div className="editorial-divider w-16" />
          </AnimatedSection>

          <div className="bento-grid">
            {features.map((f, i) => {
              const IconComponent = f.icon;
              const isAccent = i === 0;
              return (
                <AnimatedSection key={f.title} delay={i * 0.08}>
                  <div className={`card-hover rounded border p-6 h-full flex flex-col ${
                    isAccent
                      ? "border-amber/30 bg-gradient-to-br from-surface-2 to-surface-1"
                      : "border-border bg-surface-2"
                  }`}>
                    <div className={`mb-4 flex h-10 w-10 items-center justify-center rounded ${
                      isAccent ? "bg-amber/20 text-amber-bright" : "bg-amber/10 text-amber"
                    }`}>
                      <IconComponent size={20} />
                    </div>
                    <h3 className={`mb-2 font-semibold ${isAccent ? "text-lg" : ""}`}>{f.title}</h3>
                    <p className={`text-text-secondary ${isAccent ? "text-base" : "text-sm"}`}>{f.desc}</p>
                    {isAccent && (
                      <div className="mt-auto pt-4">
                        <div className="flex flex-wrap gap-1.5">
                          {["WTTJ", "RemoteOK", "Adzuna", "FranceTravail", "Indeed", "APEC"].map((s) => (
                            <span key={s} className="tag-pill">{s}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </AnimatedSection>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── How it works — Editorial Steps ─── */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <AnimatedSection className="mb-12">
            <div className="flex items-end gap-4 mb-3">
              <span className="section-number">02</span>
              <div>
                <h2 className="text-3xl font-bold" style={{ letterSpacing: "-0.03em" }}>Comment ça marche</h2>
                <p className="text-text-secondary">Trois étapes vers votre prochain poste.</p>
              </div>
            </div>
            <div className="editorial-divider w-16" />
          </AnimatedSection>

          <div className="space-y-8 sm:space-y-0 sm:grid sm:grid-cols-3 sm:gap-8">
            {steps.map((s, i) => (
              <AnimatedSection key={s.num} delay={i * 0.15}>
                <div className="relative">
                  {/* Large editorial number */}
                  <div className="font-display text-6xl text-amber/15 mb-2 italic" style={{ lineHeight: 1 }}>
                    {s.num}
                  </div>
                  {/* Connecting line */}
                  {i < steps.length - 1 && (
                    <div className="absolute top-8 left-full hidden h-px w-full bg-gradient-to-r from-amber/30 to-transparent sm:block" style={{ width: "calc(100% - 2rem)" }} />
                  )}
                  <h3 className="mb-2 text-lg font-semibold">{s.title}</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">{s.desc}</p>
                </div>
              </AnimatedSection>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Pricing — Editorial Cards ─── */}
      <section className="border-y border-border bg-surface-1 px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <AnimatedSection className="mb-12">
            <div className="flex items-end gap-4 mb-3">
              <span className="section-number">03</span>
              <div>
                <h2 className="text-3xl font-bold" style={{ letterSpacing: "-0.03em" }}>Tarifs transparents</h2>
                <p className="text-text-secondary">Commencez gratuitement, passez à la vitesse supérieure quand vous en avez besoin.</p>
              </div>
            </div>
            <div className="editorial-divider w-16" />
          </AnimatedSection>

          <div className="grid gap-8 sm:grid-cols-2">
            {/* Free */}
            <AnimatedSection>
              <div className="rounded border border-border bg-surface-2 p-8">
                <h3 className="text-lg font-semibold">Gratuit</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="font-mono text-4xl font-bold" style={{ letterSpacing: "-0.04em" }}>0 $</span>
                  <span className="text-text-muted">/mois</span>
                </div>
                <ul className="mt-6 space-y-3 text-sm text-text-secondary">
                  {["10 offres évaluées par cycle", "Tableau de bord + filtres", "Notifications email", "Export CSV"].map((t) => (
                    <li key={t} className="flex items-center gap-2">
                      <CheckIcon size={16} className="text-positive" />
                      {t}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/login"
                  className="mt-8 block rounded border border-border py-2.5 text-center text-sm font-medium text-text-secondary hover:border-border-hover hover:text-text-primary transition-colors"
                >
                  Commencer
                </Link>
              </div>
            </AnimatedSection>

            {/* Pro */}
            <AnimatedSection delay={0.1}>
              <div className="signal-glow relative rounded border-2 border-amber bg-surface-2 p-8">
                <div className="absolute -top-3 left-6 rounded bg-gradient-to-r from-amber-bright to-amber-dim px-3 py-0.5 text-xs font-medium text-surface-0">
                  Populaire
                </div>
                <h3 className="text-lg font-semibold">Pro</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="font-mono text-4xl font-bold text-amber-bright" style={{ letterSpacing: "-0.04em" }}>9 $</span>
                  <span className="text-text-muted">/mois</span>
                </div>
                <ul className="mt-6 space-y-3 text-sm text-text-secondary">
                  {[
                    "Scoring illimité des offres",
                    "Alertes Telegram instantanées",
                    "Candidature auto (CV + lettre)",
                    "Recherche entreprise IA",
                    "Support prioritaire",
                  ].map((f) => (
                    <li key={f} className="flex items-center gap-2">
                      <CheckIcon size={16} className="text-positive" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/login"
                  className="mt-8 block rounded bg-amber py-2.5 text-center text-sm font-medium text-surface-0 hover:bg-amber-bright transition-colors"
                >
                  Essai gratuit — 14 jours
                </Link>
              </div>
            </AnimatedSection>
          </div>
        </div>
      </section>

      {/* ─── CTA — Full-bleed Editorial ─── */}
      <section className="relative overflow-hidden px-6 py-20">
        <div className="hero-grid absolute inset-0 opacity-20" />
        <div className="absolute right-0 bottom-0 w-96 h-96 bg-amber/5 blur-3xl rounded-full" />

        <div className="relative mx-auto max-w-3xl">
          <AnimatedSection>
            <div className="text-center">
              <h2 className="editorial-h1 mb-6 text-text-primary">
                Prêt à trouver<br />
                <span className="text-amber-gradient">votre signal ?</span>
              </h2>
              <div className="editorial-divider mx-auto mb-8 w-16" />
              <p className="mb-10 text-lg text-text-secondary">
                Rejoignez JobScout. 14 jours d&apos;essai gratuit, annulez à tout moment.
              </p>
              <Link
                href="/login"
                className="signal-glow inline-block rounded border border-amber bg-amber px-10 py-4 text-lg font-medium text-surface-0 hover:bg-amber-bright transition-colors"
              >
                Commencer gratuitement
              </Link>
            </div>
          </AnimatedSection>
        </div>
      </section>

      {/* ─── Footer — Editorial Columns ─── */}
      <footer className="border-t border-border bg-surface-0 px-6 py-12">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-8 sm:flex-row sm:justify-between">
          <div className="flex flex-col items-center gap-3 sm:items-start">
            <Logo size="sm" />
            <span className="text-xs text-text-muted">
              &copy; {new Date().getFullYear()} JobScout. Tous droits réservés.
            </span>
          </div>
          <div className="flex gap-12 text-sm">
            <div>
              <div className="label mb-3">Produit</div>
              <nav className="flex flex-col gap-2 text-text-secondary">
                <Link href="/pricing" className="hover:text-text-primary transition-colors">Tarifs</Link>
                <Link href="/login" className="hover:text-text-primary transition-colors">Connexion</Link>
              </nav>
            </div>
            <div>
              <div className="label mb-3">Légal</div>
              <nav className="flex flex-col gap-2 text-text-secondary">
                <Link href="/legal/privacy" className="hover:text-text-primary transition-colors">Confidentialité</Link>
                <Link href="/legal/terms" className="hover:text-text-primary transition-colors">CGU</Link>
                <Link href="/legal/mentions" className="hover:text-text-primary transition-colors">Mentions légales</Link>
              </nav>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
