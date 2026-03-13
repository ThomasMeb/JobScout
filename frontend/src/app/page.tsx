import type { Metadata } from "next";
import Link from "next/link";
import Logo from "@/components/Logo";
import JsonLd from "@/components/JsonLd";
import { organizationJsonLd, softwareApplicationJsonLd } from "@/lib/structured-data";

export const metadata: Metadata = {
  title: "JobScout — Matching emploi par IA | Scraping & scoring automatique",
  description:
    "Scraping de 10+ sites d'emploi, scoring IA personnalisé de 0 à 100, candidature automatique. Trouvez votre prochain poste sans effort.",
  alternates: { canonical: "https://jobscout.mebarki.dev" },
};

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-white dark:bg-gray-950">
      <JsonLd data={organizationJsonLd()} />
      <JsonLd data={softwareApplicationJsonLd()} />
      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur dark:border-gray-800 dark:bg-gray-950/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo size="md" />
          <nav className="flex items-center gap-6">
            <Link href="/pricing" className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
              Tarifs
            </Link>
            <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
              Se connecter
            </Link>
            <Link
              href="/login"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Commencer gratuitement
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-block rounded-full border border-blue-200 bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-700 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-300">
            Matching emploi par IA
          </div>
          <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            Arrêtez de scroller les sites d&apos;emploi.
            <br />
            <span className="text-blue-600">Laissez l&apos;IA trouver votre match.</span>
          </h1>
          <p className="mx-auto mb-10 max-w-xl text-lg text-gray-600 dark:text-gray-400">
            JobScout scrape plus de 10 sites d&apos;emploi, évalue chaque offre
            par rapport à votre CV grâce à l&apos;IA, et ne vous envoie que les offres qui valent le coup.
          </p>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/login"
              className="rounded-lg bg-blue-600 px-8 py-3.5 text-lg font-medium text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700"
            >
              Essai gratuit
            </Link>
            <Link
              href="/pricing"
              className="rounded-lg border border-gray-300 px-8 py-3.5 text-lg font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-900"
            >
              Voir les tarifs
            </Link>
          </div>
          <p className="mt-4 text-sm text-gray-500">
            14 jours d&apos;essai gratuit &middot; Sans carte bancaire
          </p>
        </div>
      </section>

      {/* Stats bar */}
      <section className="border-y border-gray-200 bg-gray-50 px-6 py-10 dark:border-gray-800 dark:bg-gray-900">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-8 text-center sm:grid-cols-4">
          {[
            { value: "10+", label: "Sources d'emploi" },
            { value: "1000+", label: "Offres évaluées/jour" },
            { value: "< 5 $", label: "Par mois" },
            { value: "5 min", label: "Mise en place" },
          ].map((stat) => (
            <div key={stat.label}>
              <div className="text-2xl font-bold text-blue-600 sm:text-3xl">{stat.value}</div>
              <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <div className="mb-12 text-center">
            <h2 className="mb-3 text-3xl font-bold">Tout ce qu&apos;il faut pour décrocher votre prochain poste</h2>
            <p className="text-gray-600 dark:text-gray-400">
              Du scraping à la candidature, JobScout automatise toute votre recherche d&apos;emploi.
            </p>
          </div>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: "🔍",
                title: "Scraping multi-sources",
                desc: "WTTJ, RemoteOK, Adzuna, France Travail, Indeed, LinkedIn — tout au même endroit.",
              },
              {
                icon: "🎯",
                title: "Scoring IA de 0 à 100",
                desc: "Chaque offre évaluée par rapport à votre CV, compétences, préférences et attentes salariales.",
              },
              {
                icon: "📊",
                title: "Tableau de bord intelligent",
                desc: "Filtrez, triez et suivez vos candidatures avec des analyses en temps réel.",
              },
              {
                icon: "📱",
                title: "Notifications Telegram",
                desc: "Recevez des alertes instantanées pour les offres à haut score, directement sur votre téléphone.",
              },
              {
                icon: "📝",
                title: "Candidature automatique",
                desc: "Un clic : CV adapté, lettre de motivation et email — tout généré automatiquement.",
              },
              {
                icon: "📈",
                title: "Recherche entreprise",
                desc: "Veille automatique : taille, levées de fonds, stack technique, culture d'entreprise.",
              },
            ].map((f) => (
              <div key={f.title} className="rounded-xl border border-gray-200 p-6 dark:border-gray-800">
                <div className="mb-3 text-2xl">{f.icon}</div>
                <h4 className="mb-2 font-semibold">{f.title}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-y border-gray-200 bg-gray-50 px-6 py-20 dark:border-gray-800 dark:bg-gray-900">
        <div className="mx-auto max-w-4xl">
          <div className="mb-12 text-center">
            <h2 className="mb-3 text-3xl font-bold">Comment ça marche</h2>
            <p className="text-gray-600 dark:text-gray-400">Trois étapes vers votre prochain poste.</p>
          </div>
          <div className="grid gap-10 sm:grid-cols-3">
            {[
              {
                step: "1",
                title: "Importez votre CV",
                desc: "Indiquez vos compétences, votre expérience et ce que vous recherchez. 5 minutes de mise en place.",
              },
              {
                step: "2",
                title: "L'IA trouve vos matchs",
                desc: "Toutes les quelques heures, on scrape de nouvelles offres et on les évalue par rapport à votre profil.",
              },
              {
                step: "3",
                title: "Postulez en un clic",
                desc: "Consultez les meilleurs matchs, générez votre candidature automatiquement et envoyez-la directement.",
              },
            ].map((s) => (
              <div key={s.step} className="text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-lg font-bold text-white">
                  {s.step}
                </div>
                <h4 className="mb-2 font-semibold">{s.title}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing preview */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <div className="mb-12 text-center">
            <h2 className="mb-3 text-3xl font-bold">Tarifs simples et transparents</h2>
            <p className="text-gray-600 dark:text-gray-400">Commencez gratuitement, passez à la vitesse supérieure quand vous en avez besoin.</p>
          </div>
          <div className="grid gap-8 sm:grid-cols-2">
            {/* Free */}
            <div className="rounded-xl border border-gray-200 p-8 dark:border-gray-800">
              <h4 className="text-lg font-semibold">Gratuit</h4>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-4xl font-bold">0 $</span>
                <span className="text-gray-500">/mois</span>
              </div>
              <ul className="mt-6 space-y-3 text-sm text-gray-600 dark:text-gray-400">
                <li>10 offres évaluées par cycle</li>
                <li>Tableau de bord + filtres</li>
                <li>Notifications email</li>
                <li>Export CSV</li>
              </ul>
              <Link
                href="/login"
                className="mt-8 block rounded-lg border border-gray-300 py-2.5 text-center text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-900"
              >
                Commencer
              </Link>
            </div>
            {/* Pro */}
            <div className="relative rounded-xl border-2 border-blue-600 p-8">
              <div className="absolute -top-3 left-6 rounded-full bg-blue-600 px-3 py-0.5 text-xs font-medium text-white">
                Populaire
              </div>
              <h4 className="text-lg font-semibold">Pro</h4>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-4xl font-bold">9 $</span>
                <span className="text-gray-500">/mois</span>
              </div>
              <ul className="mt-6 space-y-3 text-sm text-gray-600 dark:text-gray-400">
                <li>Scoring illimité des offres</li>
                <li>Alertes Telegram instantanées</li>
                <li>Candidature auto (CV + lettre de motivation)</li>
                <li>Recherche entreprise IA</li>
                <li>Support prioritaire</li>
              </ul>
              <Link
                href="/login"
                className="mt-8 block rounded-lg bg-blue-600 py-2.5 text-center text-sm font-medium text-white hover:bg-blue-700"
              >
                Essai gratuit
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-blue-600 px-6 py-16">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="mb-4 text-3xl font-bold text-white">Prêt à automatiser votre recherche d&apos;emploi ?</h2>
          <p className="mb-8 text-blue-100">
            Rejoignez JobScout aujourd&apos;hui. 14 jours d&apos;essai gratuit, annulez à tout moment.
          </p>
          <Link
            href="/login"
            className="inline-block rounded-lg bg-white px-8 py-3.5 text-lg font-medium text-blue-600 hover:bg-blue-50"
          >
            Commencer gratuitement
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white px-6 py-10 dark:border-gray-800 dark:bg-gray-950">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 sm:flex-row sm:justify-between">
          <div className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} JobScout. Tous droits réservés.
          </div>
          <nav className="flex gap-6 text-sm text-gray-500">
            <Link href="/pricing" className="hover:text-gray-900 dark:hover:text-white">Tarifs</Link>
            <Link href="/legal/privacy" className="hover:text-gray-900 dark:hover:text-white">Confidentialité</Link>
            <Link href="/legal/terms" className="hover:text-gray-900 dark:hover:text-white">CGU</Link>
            <Link href="/legal/mentions" className="hover:text-gray-900 dark:hover:text-white">Mentions légales</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
