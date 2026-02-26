import Link from "next/link";
import Logo from "@/components/Logo";

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-white dark:bg-gray-950">
      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur dark:border-gray-800 dark:bg-gray-950/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo size="md" />
          <nav className="flex items-center gap-6">
            <Link href="/pricing" className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
              Pricing
            </Link>
            <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
              Sign in
            </Link>
            <Link
              href="/login"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Get started free
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-block rounded-full border border-blue-200 bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-700 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-300">
            AI-powered job matching
          </div>
          <h2 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            Stop scrolling job boards.
            <br />
            <span className="text-blue-600">Let AI find your match.</span>
          </h2>
          <p className="mx-auto mb-10 max-w-xl text-lg text-gray-600 dark:text-gray-400">
            JobScout scrapes 10+ job boards, scores every offer against your CV
            using AI, and sends you only the jobs worth applying to.
          </p>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/login"
              className="rounded-lg bg-blue-600 px-8 py-3.5 text-lg font-medium text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700"
            >
              Start free trial
            </Link>
            <Link
              href="/pricing"
              className="rounded-lg border border-gray-300 px-8 py-3.5 text-lg font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-900"
            >
              View pricing
            </Link>
          </div>
          <p className="mt-4 text-sm text-gray-500">
            14-day free trial &middot; No credit card required
          </p>
        </div>
      </section>

      {/* Stats bar */}
      <section className="border-y border-gray-200 bg-gray-50 px-6 py-10 dark:border-gray-800 dark:bg-gray-900">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-8 text-center sm:grid-cols-4">
          {[
            { value: "10+", label: "Job sources" },
            { value: "1000+", label: "Jobs scored daily" },
            { value: "< $5", label: "Per month" },
            { value: "5 min", label: "Setup time" },
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
            <h3 className="mb-3 text-3xl font-bold">Everything you need to land your next job</h3>
            <p className="text-gray-600 dark:text-gray-400">
              From scraping to applying, JobScout automates your entire job search.
            </p>
          </div>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: "🔍",
                title: "Multi-source scraping",
                desc: "WTTJ, RemoteOK, Adzuna, France Travail, Indeed, LinkedIn — all in one place.",
              },
              {
                icon: "🎯",
                title: "AI scoring 0-100",
                desc: "Each job scored against your CV, skills, preferences, and salary expectations.",
              },
              {
                icon: "📊",
                title: "Smart dashboard",
                desc: "Filter, sort, and track your applications with real-time analytics.",
              },
              {
                icon: "📱",
                title: "Telegram notifications",
                desc: "Get instant alerts for high-scoring jobs, directly on your phone.",
              },
              {
                icon: "📝",
                title: "Auto-apply pipeline",
                desc: "One click: tailored CV, cover letter, and email — all generated automatically.",
              },
              {
                icon: "📈",
                title: "Company research",
                desc: "Automatic company intelligence: size, funding, tech stack, culture insights.",
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
            <h3 className="mb-3 text-3xl font-bold">How it works</h3>
            <p className="text-gray-600 dark:text-gray-400">Three steps to your next job.</p>
          </div>
          <div className="grid gap-10 sm:grid-cols-3">
            {[
              {
                step: "1",
                title: "Upload your CV",
                desc: "Tell us your skills, experience, and what you're looking for. 5-minute setup.",
              },
              {
                step: "2",
                title: "AI matches jobs",
                desc: "Every few hours, we scrape fresh jobs and score them against your profile.",
              },
              {
                step: "3",
                title: "Apply in one click",
                desc: "Review top matches, auto-generate your application, and send it directly.",
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
            <h3 className="mb-3 text-3xl font-bold">Simple, transparent pricing</h3>
            <p className="text-gray-600 dark:text-gray-400">Start free, upgrade when you need more.</p>
          </div>
          <div className="grid gap-8 sm:grid-cols-2">
            {/* Free */}
            <div className="rounded-xl border border-gray-200 p-8 dark:border-gray-800">
              <h4 className="text-lg font-semibold">Free</h4>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-4xl font-bold">$0</span>
                <span className="text-gray-500">/month</span>
              </div>
              <ul className="mt-6 space-y-3 text-sm text-gray-600 dark:text-gray-400">
                <li>10 jobs scored per cycle</li>
                <li>Dashboard + filters</li>
                <li>Email notifications</li>
                <li>CSV export</li>
              </ul>
              <Link
                href="/login"
                className="mt-8 block rounded-lg border border-gray-300 py-2.5 text-center text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-900"
              >
                Get started
              </Link>
            </div>
            {/* Pro */}
            <div className="relative rounded-xl border-2 border-blue-600 p-8">
              <div className="absolute -top-3 left-6 rounded-full bg-blue-600 px-3 py-0.5 text-xs font-medium text-white">
                Popular
              </div>
              <h4 className="text-lg font-semibold">Pro</h4>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-4xl font-bold">$9</span>
                <span className="text-gray-500">/month</span>
              </div>
              <ul className="mt-6 space-y-3 text-sm text-gray-600 dark:text-gray-400">
                <li>Unlimited job scoring</li>
                <li>Telegram instant alerts</li>
                <li>Auto-apply pipeline (CV + cover letter)</li>
                <li>Company research AI</li>
                <li>Priority support</li>
              </ul>
              <Link
                href="/login"
                className="mt-8 block rounded-lg bg-blue-600 py-2.5 text-center text-sm font-medium text-white hover:bg-blue-700"
              >
                Start free trial
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-blue-600 px-6 py-16">
        <div className="mx-auto max-w-2xl text-center">
          <h3 className="mb-4 text-3xl font-bold text-white">Ready to automate your job search?</h3>
          <p className="mb-8 text-blue-100">
            Join JobScout today. 14-day free trial, cancel anytime.
          </p>
          <Link
            href="/login"
            className="inline-block rounded-lg bg-white px-8 py-3.5 text-lg font-medium text-blue-600 hover:bg-blue-50"
          >
            Get started free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white px-6 py-10 dark:border-gray-800 dark:bg-gray-950">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 sm:flex-row sm:justify-between">
          <div className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} JobScout. All rights reserved.
          </div>
          <nav className="flex gap-6 text-sm text-gray-500">
            <Link href="/pricing" className="hover:text-gray-900 dark:hover:text-white">Pricing</Link>
            <Link href="/legal/privacy" className="hover:text-gray-900 dark:hover:text-white">Privacy</Link>
            <Link href="/legal/terms" className="hover:text-gray-900 dark:hover:text-white">Terms</Link>
            <Link href="/legal/mentions" className="hover:text-gray-900 dark:hover:text-white">Legal</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
