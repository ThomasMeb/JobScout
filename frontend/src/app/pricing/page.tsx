import type { Metadata } from "next";
import Link from "next/link";
import Logo from "@/components/Logo";
import JsonLd from "@/components/JsonLd";
import { faqJsonLd } from "@/lib/structured-data";
import { CheckIcon, CrossIcon } from "@/components/Icons";
import ThemeToggle from "@/components/ThemeToggle";

export const metadata: Metadata = {
  title: "Tarifs",
  description:
    "Plans Gratuit et Pro pour JobScout. Essai gratuit 14 jours, scoring IA illimité, alertes Telegram, candidature automatique dès 9$/mois.",
  alternates: { canonical: "https://jobscout.mebarki.dev/pricing" },
};

const plans = [
  {
    name: "Gratuit",
    price: "0 $",
    period: "/mois",
    description: "Parfait pour démarrer et découvrir la plateforme.",
    cta: "Commencer",
    popular: false,
    features: [
      { text: "10 offres évaluées par cycle", included: true },
      { text: "Tableau de bord avec filtres", included: true },
      { text: "Notifications email", included: true },
      { text: "Export CSV", included: true },
      { text: "Alertes Telegram instantanées", included: false },
      { text: "Candidature automatique", included: false },
      { text: "Recherche entreprise IA", included: false },
      { text: "Support prioritaire", included: false },
    ],
  },
  {
    name: "Pro",
    price: "9 $",
    period: "/mois",
    description: "Pour les chercheurs d'emploi actifs qui veulent un maximum d'automatisation.",
    cta: "Démarrer l'essai gratuit",
    popular: true,
    features: [
      { text: "Évaluation illimitée des offres", included: true },
      { text: "Tableau de bord avec filtres", included: true },
      { text: "Notifications email", included: true },
      { text: "Export CSV", included: true },
      { text: "Alertes Telegram instantanées", included: true },
      { text: "Candidature automatique", included: true },
      { text: "Recherche entreprise IA", included: true },
      { text: "Support prioritaire", included: true },
    ],
  },
];

const faqs = [
  {
    q: "Comment fonctionne l'essai gratuit ?",
    a: "Vous bénéficiez d'un accès Pro complet pendant 14 jours. Aucune carte bancaire requise. À la fin de l'essai, vous pouvez choisir de passer à Pro ou de continuer avec le plan Gratuit.",
  },
  {
    q: "Puis-je annuler à tout moment ?",
    a: "Oui, vous pouvez annuler votre abonnement à tout moment. Vous conservez l'accès Pro jusqu'à la fin de votre période de facturation en cours.",
  },
  {
    q: "Quels sites d'emploi sont parcourus ?",
    a: "Nous parcourons Welcome to the Jungle, RemoteOK, Adzuna, France Travail, Indeed, LinkedIn et d'autres. De nouvelles sources sont ajoutées régulièrement.",
  },
  {
    q: "Comment fonctionne le scoring IA ?",
    a: "Chaque offre est notée de 0 à 100 selon 5 critères : correspondance des compétences, niveau d'expérience, adéquation lieu/télétravail, alignement salarial et préférences de type de poste. Propulsé par DeepSeek AI.",
  },
  {
    q: "Mes données sont-elles en sécurité ?",
    a: "Vos données sont stockées de manière sécurisée sur Supabase (PostgreSQL) avec une sécurité au niveau des lignes. Nous ne partageons jamais votre CV ni vos informations personnelles avec des tiers.",
  },
];

export default function PricingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-surface-0 text-text-primary">
      <JsonLd data={faqJsonLd(faqs.map((f) => ({ question: f.q, answer: f.a })))} />

      {/* Navbar */}
      <header className="border-b border-border bg-surface-0/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/"><Logo size="md" /></Link>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link href="/login" className="rounded bg-amber px-4 py-2 text-sm font-medium text-surface-0 hover:bg-amber-bright transition-colors">
              Commencer
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1 px-6 py-16">
        <div className="mx-auto max-w-4xl">
          {/* Header */}
          <div className="mb-12 text-center">
            <h1 className="mb-3 text-4xl font-bold" style={{ letterSpacing: "-0.03em" }}>
              Des tarifs simples et transparents
            </h1>
            <p className="text-lg text-text-secondary">
              Commencez gratuitement, passez à Pro quand vous en avez besoin. Annulez à tout moment.
            </p>
          </div>

          {/* Plans */}
          <div className="grid gap-8 sm:grid-cols-2">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded border p-8 ${
                  plan.popular
                    ? "signal-glow border-2 border-amber bg-surface-1"
                    : "border-border bg-surface-1"
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-6 rounded bg-gradient-to-r from-amber-bright to-amber-dim px-3 py-0.5 text-xs font-medium text-surface-0">
                    Le plus populaire
                  </div>
                )}
                <h2 className="text-lg font-semibold">{plan.name}</h2>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className={`font-mono text-4xl font-bold ${plan.popular ? "text-amber-bright" : ""}`}>{plan.price}</span>
                  <span className="text-text-muted">{plan.period}</span>
                </div>
                <p className="mt-2 text-sm text-text-secondary">{plan.description}</p>

                <Link
                  href="/login"
                  className={`mt-6 block rounded py-2.5 text-center text-sm font-medium transition-colors ${
                    plan.popular
                      ? "bg-amber text-surface-0 hover:bg-amber-bright"
                      : "border border-border text-text-secondary hover:border-border-hover hover:text-text-primary"
                  }`}
                >
                  {plan.cta}
                </Link>

                <ul className="mt-8 space-y-3">
                  {plan.features.map((f) => (
                    <li key={f.text} className="flex items-start gap-3 text-sm">
                      {f.included ? (
                        <CheckIcon size={16} className="mt-0.5 text-positive" />
                      ) : (
                        <CrossIcon size={16} className="mt-0.5 text-text-muted" />
                      )}
                      <span className={f.included ? "text-text-secondary" : "text-text-muted"}>
                        {f.text}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* FAQ */}
          <div className="mt-20">
            <h2 className="mb-8 text-center text-2xl font-bold" style={{ letterSpacing: "-0.03em" }}>
              Questions fréquentes
            </h2>
            <div className="space-y-4">
              {faqs.map((faq) => (
                <details key={faq.q} className="group rounded border border-border bg-surface-1">
                  <summary className="cursor-pointer px-6 py-4 font-medium text-text-primary hover:text-amber transition-colors list-none flex items-center justify-between">
                    {faq.q}
                    <span className="text-text-muted transition-transform group-open:rotate-180">&#9662;</span>
                  </summary>
                  <div className="border-t border-border px-6 py-4 text-sm text-text-secondary">
                    {faq.a}
                  </div>
                </details>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
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
