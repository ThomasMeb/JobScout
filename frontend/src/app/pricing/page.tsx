import type { Metadata } from "next";
import Link from "next/link";
import Logo from "@/components/Logo";
import JsonLd from "@/components/JsonLd";
import { faqJsonLd } from "@/lib/structured-data";

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
    ctaStyle: "border border-gray-300 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-900",
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
    ctaStyle: "bg-blue-600 text-white hover:bg-blue-700",
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
    <div className="flex min-h-screen flex-col bg-white dark:bg-gray-950">
      <JsonLd
        data={faqJsonLd(
          faqs.map((f) => ({ question: f.q, answer: f.a }))
        )}
      />
      {/* Navbar */}
      <header className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/"><Logo size="md" /></Link>
          <Link
            href="/login"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Commencer
          </Link>
        </div>
      </header>

      <main className="flex-1 px-6 py-16">
        <div className="mx-auto max-w-4xl">
          {/* Header */}
          <div className="mb-12 text-center">
            <h2 className="mb-3 text-4xl font-bold">Des tarifs simples et transparents</h2>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Commencez gratuitement, passez à Pro quand vous en avez besoin. Annulez à tout moment.
            </p>
          </div>

          {/* Plans */}
          <div className="grid gap-8 sm:grid-cols-2">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-xl p-8 ${
                  plan.popular
                    ? "border-2 border-blue-600"
                    : "border border-gray-200 dark:border-gray-800"
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-6 rounded-full bg-blue-600 px-3 py-0.5 text-xs font-medium text-white">
                    Le plus populaire
                  </div>
                )}
                <h3 className="text-lg font-semibold">{plan.name}</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-gray-500">{plan.period}</span>
                </div>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{plan.description}</p>

                <Link
                  href="/login"
                  className={`mt-6 block rounded-lg py-2.5 text-center text-sm font-medium ${plan.ctaStyle}`}
                >
                  {plan.cta}
                </Link>

                <ul className="mt-8 space-y-3">
                  {plan.features.map((f) => (
                    <li key={f.text} className="flex items-start gap-3 text-sm">
                      <span className={f.included ? "text-green-600" : "text-gray-300 dark:text-gray-600"}>
                        {f.included ? "✓" : "—"}
                      </span>
                      <span className={f.included ? "" : "text-gray-400 dark:text-gray-600"}>
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
            <h3 className="mb-8 text-center text-2xl font-bold">Questions fréquentes</h3>
            <div className="space-y-6">
              {faqs.map((faq) => (
                <div key={faq.q} className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
                  <h4 className="font-semibold">{faq.q}</h4>
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{faq.a}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 px-6 py-8 dark:border-gray-800">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <div className="text-sm text-gray-500">&copy; {new Date().getFullYear()} JobScout</div>
          <nav className="flex gap-6 text-sm text-gray-500">
            <Link href="/legal/privacy" className="hover:text-gray-900 dark:hover:text-white">Confidentialité</Link>
            <Link href="/legal/terms" className="hover:text-gray-900 dark:hover:text-white">CGU</Link>
            <Link href="/legal/mentions" className="hover:text-gray-900 dark:hover:text-white">Mentions légales</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
