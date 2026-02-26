import Link from "next/link";
import Logo from "@/components/Logo";

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "/month",
    description: "Perfect to get started and explore the platform.",
    cta: "Get started",
    ctaStyle: "border border-gray-300 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-900",
    popular: false,
    features: [
      { text: "10 jobs scored per cycle", included: true },
      { text: "Dashboard with filters", included: true },
      { text: "Email notifications", included: true },
      { text: "CSV export", included: true },
      { text: "Telegram instant alerts", included: false },
      { text: "Auto-apply pipeline", included: false },
      { text: "Company research AI", included: false },
      { text: "Priority support", included: false },
    ],
  },
  {
    name: "Pro",
    price: "$9",
    period: "/month",
    description: "For active job seekers who want maximum automation.",
    cta: "Start free trial",
    ctaStyle: "bg-blue-600 text-white hover:bg-blue-700",
    popular: true,
    features: [
      { text: "Unlimited job scoring", included: true },
      { text: "Dashboard with filters", included: true },
      { text: "Email notifications", included: true },
      { text: "CSV export", included: true },
      { text: "Telegram instant alerts", included: true },
      { text: "Auto-apply pipeline", included: true },
      { text: "Company research AI", included: true },
      { text: "Priority support", included: true },
    ],
  },
];

const faqs = [
  {
    q: "How does the free trial work?",
    a: "You get full Pro access for 14 days. No credit card required. At the end of the trial, you can choose to upgrade or continue with the Free plan.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Yes, you can cancel your subscription at any time. You'll keep Pro access until the end of your current billing period.",
  },
  {
    q: "Which job boards do you scrape?",
    a: "We scrape Welcome to the Jungle, RemoteOK, Adzuna, France Travail, Indeed, LinkedIn, and more. New sources are added regularly.",
  },
  {
    q: "How does AI scoring work?",
    a: "Each job is scored 0-100 based on 5 criteria: skills match, experience level, location/remote fit, salary alignment, and job type preferences. Powered by DeepSeek AI.",
  },
  {
    q: "Is my data secure?",
    a: "Your data is stored securely on Supabase (PostgreSQL) with row-level security. We never share your CV or personal information with third parties.",
  },
];

export default function PricingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-white dark:bg-gray-950">
      {/* Navbar */}
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

      <main className="flex-1 px-6 py-16">
        <div className="mx-auto max-w-4xl">
          {/* Header */}
          <div className="mb-12 text-center">
            <h2 className="mb-3 text-4xl font-bold">Simple, transparent pricing</h2>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Start free, upgrade when you need more. Cancel anytime.
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
                    Most popular
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
            <h3 className="mb-8 text-center text-2xl font-bold">Frequently asked questions</h3>
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
            <Link href="/legal/privacy" className="hover:text-gray-900 dark:hover:text-white">Privacy</Link>
            <Link href="/legal/terms" className="hover:text-gray-900 dark:hover:text-white">Terms</Link>
            <Link href="/legal/mentions" className="hover:text-gray-900 dark:hover:text-white">Legal</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
