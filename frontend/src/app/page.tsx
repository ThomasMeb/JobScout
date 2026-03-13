import type { Metadata } from "next";
import Link from "next/link";
import Logo from "@/components/Logo";
import JsonLd from "@/components/JsonLd";
import AnimatedSection from "@/components/AnimatedSection";
import { organizationJsonLd, softwareApplicationJsonLd } from "@/lib/structured-data";
import { SearchIcon, TargetIcon, ChartIcon, BellIcon, PenIcon, TrendingIcon, CheckIcon, CrossIcon } from "@/components/Icons";

export const metadata: Metadata = {
  title: "JobScout — Matching emploi par IA | Scraping & scoring automatique",
  description:
    "Scraping de 10+ sites d'emploi, scoring IA personnalisé de 0 à 100, candidature automatique. Trouvez votre prochain poste sans effort.",
  alternates: { canonical: "https://jobscout.mebarki.dev" },
};

const stats = [
  { value: "10+", label: "Sources d'emploi" },
  { value: "1000+", label: "Offres évaluées/jour" },
  { value: "< 5 $", label: "Par mois" },
  { value: "5 min", label: "Mise en place" },
];

const features = [
  { icon: SearchIcon, title: "Scraping multi-sources", desc: "WTTJ, RemoteOK, Adzuna, France Travail, Indeed, LinkedIn — tout au même endroit." },
  { icon: TargetIcon, title: "Scoring IA de 0 à 100", desc: "Chaque offre évaluée par rapport à votre CV, compétences, préférences et attentes salariales." },
  { icon: ChartIcon, title: "Tableau de bord intelligent", desc: "Filtrez, triez et suivez vos candidatures avec des analyses en temps réel." },
  { icon: BellIcon, title: "Notifications Telegram", desc: "Recevez des alertes instantanées pour les offres à haut score, directement sur votre téléphone." },
  { icon: PenIcon, title: "Candidature automatique", desc: "Un clic : CV adapté, lettre de motivation et email — tout généré automatiquement." },
  { icon: TrendingIcon, title: "Recherche entreprise", desc: "Veille automatique : taille, levées de fonds, stack technique, culture d'entreprise." },
];

const steps = [
  { step: "1", title: "Importez votre CV", desc: "Indiquez vos compétences, votre expérience et ce que vous recherchez. 5 minutes de mise en place." },
  { step: "2", title: "L'IA trouve vos matchs", desc: "Toutes les quelques heures, on scrape de nouvelles offres et on les évalue par rapport à votre profil." },
  { step: "3", title: "Postulez en un clic", desc: "Consultez les meilleurs matchs, générez votre candidature automatiquement et envoyez-la directement." },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-surface-0 text-text-primary">
      <JsonLd data={organizationJsonLd()} />
      <JsonLd data={softwareApplicationJsonLd()} />

      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-border bg-surface-0/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo size="md" />
          <nav className="flex items-center gap-6">
            <Link href="/pricing" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Tarifs
            </Link>
            <Link href="/login" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Se connecter
            </Link>
            <Link
              href="/login"
              className="rounded bg-amber px-4 py-2 text-sm font-medium text-surface-0 hover:bg-amber-bright transition-colors"
            >
              Commencer gratuitement
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden px-6 py-24 sm:py-32">
        {/* Dot grid background */}
        <div className="hero-grid absolute inset-0 opacity-40" />
        {/* Amber radial glow */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-amber/5 blur-3xl" />

        <div className="relative mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-block rounded border border-amber/20 bg-amber/5 px-4 py-1.5 font-mono text-xs font-medium uppercase tracking-widest text-amber">
            Matching emploi par IA
          </div>
          <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl" style={{ letterSpacing: "-0.03em" }}>
            Arrêtez de scroller les sites d&apos;emploi.
            <br />
            <span className="text-amber-gradient">Laissez l&apos;IA trouver votre match.</span>
          </h1>
          <p className="mx-auto mb-10 max-w-xl text-lg text-text-secondary">
            JobScout scrape plus de 10 sites d&apos;emploi, évalue chaque offre
            par rapport à votre CV grâce à l&apos;IA, et ne vous envoie que les offres qui valent le coup.
          </p>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/login"
              className="signal-glow rounded border border-amber bg-amber px-8 py-3.5 text-lg font-medium text-surface-0 hover:bg-amber-bright transition-colors"
            >
              Essai gratuit
            </Link>
            <Link
              href="/pricing"
              className="rounded border border-border px-8 py-3.5 text-lg font-medium text-text-secondary hover:border-border-hover hover:text-text-primary transition-colors"
            >
              Voir les tarifs
            </Link>
          </div>
          <p className="mt-4 text-sm text-text-muted">
            14 jours d&apos;essai gratuit &middot; Sans carte bancaire
          </p>
        </div>
      </section>

      {/* Stats bar */}
      <section className="border-y border-border bg-surface-1 px-6 py-10">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-8 text-center sm:grid-cols-4">
          {stats.map((stat) => (
            <AnimatedSection key={stat.label}>
              <div className="border-l-2 border-amber pl-4 text-left">
                <div className="font-mono text-2xl font-bold text-amber-bright sm:text-3xl">{stat.value}</div>
                <div className="mt-1 text-sm text-text-secondary">{stat.label}</div>
              </div>
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <AnimatedSection className="mb-12 text-center">
            <h2 className="mb-3 text-3xl font-bold" style={{ letterSpacing: "-0.03em" }}>
              Tout ce qu&apos;il faut pour décrocher votre prochain poste
            </h2>
            <p className="text-text-secondary">
              Du scraping à la candidature, JobScout automatise toute votre recherche d&apos;emploi.
            </p>
          </AnimatedSection>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f, i) => {
              const IconComponent = f.icon;
              return (
                <AnimatedSection key={f.title} delay={i * 0.1}>
                  <div className="card-hover rounded border border-border bg-surface-1 p-6">
                    <div className="mb-4 flex h-10 w-10 items-center justify-center rounded bg-amber/10 text-amber">
                      <IconComponent size={20} />
                    </div>
                    <h3 className="mb-2 font-semibold">{f.title}</h3>
                    <p className="text-sm text-text-secondary">{f.desc}</p>
                  </div>
                </AnimatedSection>
              );
            })}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-y border-border bg-surface-1 px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <AnimatedSection className="mb-12 text-center">
            <h2 className="mb-3 text-3xl font-bold" style={{ letterSpacing: "-0.03em" }}>Comment ça marche</h2>
            <p className="text-text-secondary">Trois étapes vers votre prochain poste.</p>
          </AnimatedSection>
          <div className="grid gap-10 sm:grid-cols-3">
            {steps.map((s, i) => (
              <AnimatedSection key={s.step} delay={i * 0.15}>
                <div className="relative text-center">
                  {/* Connector line */}
                  {i < steps.length - 1 && (
                    <div className="absolute left-1/2 top-6 hidden h-px w-full bg-border sm:block" />
                  )}
                  <div className="relative mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-amber-bright to-amber-dim text-lg font-bold text-surface-0">
                    {s.step}
                  </div>
                  <h3 className="mb-2 font-semibold">{s.title}</h3>
                  <p className="text-sm text-text-secondary">{s.desc}</p>
                </div>
              </AnimatedSection>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing preview */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <AnimatedSection className="mb-12 text-center">
            <h2 className="mb-3 text-3xl font-bold" style={{ letterSpacing: "-0.03em" }}>Tarifs simples et transparents</h2>
            <p className="text-text-secondary">Commencez gratuitement, passez à la vitesse supérieure quand vous en avez besoin.</p>
          </AnimatedSection>
          <div className="grid gap-8 sm:grid-cols-2">
            {/* Free */}
            <AnimatedSection>
              <div className="rounded border border-border bg-surface-1 p-8">
                <h3 className="text-lg font-semibold">Gratuit</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="font-mono text-4xl font-bold">0 $</span>
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
              <div className="signal-glow relative rounded border-2 border-amber bg-surface-1 p-8">
                <div className="absolute -top-3 left-6 rounded bg-gradient-to-r from-amber-bright to-amber-dim px-3 py-0.5 text-xs font-medium text-surface-0">
                  Populaire
                </div>
                <h3 className="text-lg font-semibold">Pro</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="font-mono text-4xl font-bold text-amber-bright">9 $</span>
                  <span className="text-text-muted">/mois</span>
                </div>
                <ul className="mt-6 space-y-3 text-sm text-text-secondary">
                  {[
                    { text: "Scoring illimité des offres", ok: true },
                    { text: "Alertes Telegram instantanées", ok: true },
                    { text: "Candidature auto (CV + lettre)", ok: true },
                    { text: "Recherche entreprise IA", ok: true },
                    { text: "Support prioritaire", ok: true },
                  ].map((f) => (
                    <li key={f.text} className="flex items-center gap-2">
                      <CheckIcon size={16} className="text-positive" />
                      {f.text}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/login"
                  className="mt-8 block rounded bg-amber py-2.5 text-center text-sm font-medium text-surface-0 hover:bg-amber-bright transition-colors"
                >
                  Essai gratuit
                </Link>
              </div>
            </AnimatedSection>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden border-y border-border bg-gradient-to-b from-surface-2 to-surface-1 px-6 py-16">
        <div className="hero-grid absolute inset-0 opacity-20" />
        <div className="relative mx-auto max-w-2xl text-center">
          <h2 className="mb-4 text-3xl font-bold" style={{ letterSpacing: "-0.03em" }}>
            Prêt à automatiser votre recherche d&apos;emploi ?
          </h2>
          <p className="mb-8 text-text-secondary">
            Rejoignez JobScout aujourd&apos;hui. 14 jours d&apos;essai gratuit, annulez à tout moment.
          </p>
          <Link
            href="/login"
            className="signal-glow inline-block rounded border border-amber bg-amber px-8 py-3.5 text-lg font-medium text-surface-0 hover:bg-amber-bright transition-colors"
          >
            Commencer gratuitement
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-surface-0 px-6 py-10">
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
