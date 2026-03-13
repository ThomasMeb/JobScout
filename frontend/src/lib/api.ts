import {
  isMockMode,
  MOCK_PROFILE,
  MOCK_STATS,
  MOCK_CHART_DATA,
  MOCK_SCRAPE_RUNS,
  MOCK_JOBS,
  MOCK_BILLING,
  MOCK_ADMIN_USERS,
  MOCK_ADMIN_SCRAPERS,
  MOCK_ADMIN_METRICS,
  getMockJobs,
} from "./mock-data";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Track if backend is unreachable to skip repeated failing calls
let _backendDown = false;

export function isBackendDown() {
  return _backendDown;
}

async function fetchAPI(path: string, options: RequestInit = {}) {
  if (_backendDown) throw new Error("Backend unavailable");

  const { createClient } = await import("./supabase-browser");
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (session?.access_token) {
    headers["Authorization"] = `Bearer ${session.access_token}`;
  }

  try {
    const res = await fetch(`${API_URL}${path}`, { ...options, headers });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || "Erreur API");
    }
    return res.json();
  } catch (e) {
    // Network error = backend is down → enable fallback
    if (e instanceof TypeError || (e instanceof Error && e.message.includes("fetch"))) {
      _backendDown = true;
    }
    throw e;
  }
}

// Helper: try real API, fall back to mock on failure
function withFallback<T>(apiFn: () => Promise<T>, mockValue: T): Promise<T> {
  if (isMockMode() || _backendDown) return Promise.resolve(mockValue);
  return apiFn().catch(() => mockValue);
}

// Profile
export const getProfile = () =>
  withFallback(() => fetchAPI("/api/profile/"), MOCK_PROFILE);

export const updateProfile = (data: Record<string, unknown>) =>
  withFallback(
    () => fetchAPI("/api/profile/", { method: "PATCH", body: JSON.stringify(data) }),
    { ...MOCK_PROFILE, ...data } as typeof MOCK_PROFILE,
  );

// Jobs
export interface JobFilters {
  page?: number;
  per_page?: number;
  min_score?: number;
  status?: string;
  source?: string;
  search?: string;
}

export const getJobs = (filters: JobFilters = {}) => {
  const mockResult = getMockJobs(filters);
  if (isMockMode() || _backendDown) return Promise.resolve(mockResult);

  const params = new URLSearchParams();
  if (filters.page) params.set("page", String(filters.page));
  if (filters.per_page) params.set("per_page", String(filters.per_page));
  if (filters.min_score) params.set("min_score", String(filters.min_score));
  if (filters.status) params.set("status", filters.status);
  if (filters.source) params.set("source", filters.source);
  if (filters.search) params.set("search", filters.search);
  return fetchAPI(`/api/jobs/?${params}`).catch(() => mockResult);
};

export const bulkFeedback = (jobIds: number[], status: string) => {
  const mockFn = () => {
    jobIds.forEach((id) => {
      const job = MOCK_JOBS.find((j) => j.id === id);
      if (job) job.status = status;
    });
    return { updated: jobIds.length };
  };
  if (isMockMode() || _backendDown) return Promise.resolve(mockFn());
  return fetchAPI("/api/jobs/bulk/feedback", {
    method: "PATCH",
    body: JSON.stringify({ job_ids: jobIds, status }),
  }).catch(() => mockFn());
};

export const getJob = (id: number) => {
  const job = MOCK_JOBS.find((j) => j.id === id);
  if (isMockMode() || _backendDown) {
    return job ? Promise.resolve(job) : Promise.reject(new Error("Job not found"));
  }
  return fetchAPI(`/api/jobs/${id}`).catch(() => {
    if (job) return job;
    throw new Error("Job not found");
  });
};

export const updateJobFeedback = (id: number, status: string, notes?: string) => {
  const mockFn = () => {
    const job = MOCK_JOBS.find((j) => j.id === id);
    if (job) {
      job.status = status;
      if (notes !== undefined) job.user_notes = notes;
    }
    return job;
  };
  if (isMockMode() || _backendDown) return Promise.resolve(mockFn());
  return fetchAPI(`/api/jobs/${id}/feedback`, {
    method: "PATCH",
    body: JSON.stringify({ status, user_notes: notes }),
  }).catch(() => mockFn());
};

// Export
export const exportJobsCSV = async (filters: JobFilters = {}) => {
  if (isMockMode()) {
    const { jobs } = getMockJobs(filters);
    const header = "title,company,score,status,source,location\n";
    const rows = jobs.map((j) => `"${j.title}","${j.company}",${j.match_score},"${j.status}","${j.source}","${j.location}"`).join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "jobscout-export.csv";
    a.click();
    window.URL.revokeObjectURL(url);
    return;
  }

  const params = new URLSearchParams();
  if (filters.min_score) params.set("min_score", String(filters.min_score));
  if (filters.status) params.set("status", filters.status);
  const query = params.toString();
  const path = `/api/jobs/export/csv${query ? `?${query}` : ""}`;

  const { createClient } = await import("./supabase-browser");
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const headers: Record<string, string> = {};
  if (session?.access_token) {
    headers["Authorization"] = `Bearer ${session.access_token}`;
  }

  const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const res = await fetch(`${API_URL}${path}`, { headers });
  if (!res.ok) throw new Error("Échec de l'export");

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "jobscout-export.csv";
  a.click();
  window.URL.revokeObjectURL(url);
};

// Account
export const deleteAccount = () =>
  withFallback(() => fetchAPI("/api/profile/", { method: "DELETE" }), { ok: true });

// Billing
export const getBillingStatus = () =>
  withFallback(() => fetchAPI("/api/billing/status"), MOCK_BILLING);

export const createCheckout = () =>
  withFallback(() => fetchAPI("/api/billing/checkout", { method: "POST" }), { url: "/dashboard/billing" });

export const createPortal = () =>
  withFallback(() => fetchAPI("/api/billing/portal", { method: "POST" }), { url: "/dashboard/billing" });

// Admin
export const getAdminUsers = () =>
  withFallback(() => fetchAPI("/api/admin/users"), MOCK_ADMIN_USERS);

export const getAdminScrapers = () =>
  withFallback(() => fetchAPI("/api/admin/scrapers"), MOCK_ADMIN_SCRAPERS);

export const getAdminMetrics = () =>
  withFallback(() => fetchAPI("/api/admin/metrics"), MOCK_ADMIN_METRICS);

// Stats
export const getStats = () =>
  withFallback(() => fetchAPI("/api/stats/"), MOCK_STATS);

// Charts
export const getChartData = () =>
  withFallback(() => fetchAPI("/api/stats/charts"), MOCK_CHART_DATA);

// Scrape runs
export const getScrapeRuns = (limit = 10) =>
  withFallback(() => fetchAPI(`/api/scrape-runs/?limit=${limit}`), MOCK_SCRAPE_RUNS.slice(0, limit));
