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

async function fetchAPI(path: string, options: RequestInit = {}) {
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

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "Erreur API");
  }

  return res.json();
}

// Profile
export const getProfile = () =>
  isMockMode() ? Promise.resolve(MOCK_PROFILE) : fetchAPI("/api/profile/");

export const updateProfile = (data: Record<string, unknown>) =>
  isMockMode()
    ? Promise.resolve({ ...MOCK_PROFILE, ...data })
    : fetchAPI("/api/profile/", { method: "PATCH", body: JSON.stringify(data) });

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
  if (isMockMode()) return Promise.resolve(getMockJobs(filters));

  const params = new URLSearchParams();
  if (filters.page) params.set("page", String(filters.page));
  if (filters.per_page) params.set("per_page", String(filters.per_page));
  if (filters.min_score) params.set("min_score", String(filters.min_score));
  if (filters.status) params.set("status", filters.status);
  if (filters.source) params.set("source", filters.source);
  if (filters.search) params.set("search", filters.search);
  return fetchAPI(`/api/jobs/?${params}`);
};

export const bulkFeedback = (jobIds: number[], status: string) => {
  if (isMockMode()) {
    jobIds.forEach((id) => {
      const job = MOCK_JOBS.find((j) => j.id === id);
      if (job) job.status = status;
    });
    return Promise.resolve({ updated: jobIds.length });
  }
  return fetchAPI("/api/jobs/bulk/feedback", {
    method: "PATCH",
    body: JSON.stringify({ job_ids: jobIds, status }),
  });
};

export const getJob = (id: number) => {
  if (isMockMode()) {
    const job = MOCK_JOBS.find((j) => j.id === id);
    return job ? Promise.resolve(job) : Promise.reject(new Error("Job not found"));
  }
  return fetchAPI(`/api/jobs/${id}`);
};

export const updateJobFeedback = (id: number, status: string, notes?: string) => {
  if (isMockMode()) {
    const job = MOCK_JOBS.find((j) => j.id === id);
    if (job) {
      job.status = status;
      if (notes !== undefined) job.user_notes = notes;
    }
    return Promise.resolve(job);
  }
  return fetchAPI(`/api/jobs/${id}/feedback`, {
    method: "PATCH",
    body: JSON.stringify({ status, user_notes: notes }),
  });
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
  isMockMode() ? Promise.resolve({ ok: true }) : fetchAPI("/api/profile/", { method: "DELETE" });

// Billing
export const getBillingStatus = () =>
  isMockMode() ? Promise.resolve(MOCK_BILLING) : fetchAPI("/api/billing/status");

export const createCheckout = () =>
  isMockMode()
    ? Promise.resolve({ url: "/dashboard/billing" })
    : fetchAPI("/api/billing/checkout", { method: "POST" });

export const createPortal = () =>
  isMockMode()
    ? Promise.resolve({ url: "/dashboard/billing" })
    : fetchAPI("/api/billing/portal", { method: "POST" });

// Admin
export const getAdminUsers = () =>
  isMockMode() ? Promise.resolve(MOCK_ADMIN_USERS) : fetchAPI("/api/admin/users");

export const getAdminScrapers = () =>
  isMockMode() ? Promise.resolve(MOCK_ADMIN_SCRAPERS) : fetchAPI("/api/admin/scrapers");

export const getAdminMetrics = () =>
  isMockMode() ? Promise.resolve(MOCK_ADMIN_METRICS) : fetchAPI("/api/admin/metrics");

// Stats
export const getStats = () =>
  isMockMode() ? Promise.resolve(MOCK_STATS) : fetchAPI("/api/stats/");

// Charts
export const getChartData = () =>
  isMockMode() ? Promise.resolve(MOCK_CHART_DATA) : fetchAPI("/api/stats/charts");

// Scrape runs
export const getScrapeRuns = (limit = 10) =>
  isMockMode()
    ? Promise.resolve(MOCK_SCRAPE_RUNS.slice(0, limit))
    : fetchAPI(`/api/scrape-runs/?limit=${limit}`);
