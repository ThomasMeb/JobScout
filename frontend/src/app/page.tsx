import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <h1 className="text-xl font-bold">
            <span className="text-blue-600">Job</span>Scout
          </h1>
          <Link
            href="/login"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Get started
          </Link>
        </div>
      </header>

      {/* Hero */}
      <main className="flex flex-1 items-center justify-center px-6">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl">
            AI-powered job matching,
            <br />
            <span className="text-blue-600">personalized for you</span>
          </h2>
          <p className="mb-8 text-lg text-gray-600 dark:text-gray-400">
            JobScout scrapes 10+ job boards, scores each offer against your profile
            using AI, and delivers only the jobs that match. Upload your CV, set your
            preferences, and let the agent work for you.
          </p>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/login"
              className="rounded-lg bg-blue-600 px-8 py-3 text-lg font-medium text-white hover:bg-blue-700"
            >
              Start free
            </Link>
            <p className="text-sm text-gray-500">No credit card required</p>
          </div>

          {/* Features */}
          <div className="mt-16 grid gap-8 text-left sm:grid-cols-3">
            <div>
              <div className="mb-2 text-2xl">🔍</div>
              <h3 className="mb-1 font-semibold">Multi-source scraping</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                WTTJ, RemoteOK, Adzuna, France Travail, Indeed, LinkedIn and more.
              </p>
            </div>
            <div>
              <div className="mb-2 text-2xl">🎯</div>
              <h3 className="mb-1 font-semibold">AI scoring</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Each job scored 0-100 against your CV with a 5-criteria breakdown.
              </p>
            </div>
            <div>
              <div className="mb-2 text-2xl">💰</div>
              <h3 className="mb-1 font-semibold">Costs under $5/month</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Powered by DeepSeek — hundreds of jobs scored for pennies.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
