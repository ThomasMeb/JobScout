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
export const getProfile = () => fetchAPI("/api/profile/");
export const updateProfile = (data: Record<string, unknown>) =>
  fetchAPI("/api/profile/", { method: "PATCH", body: JSON.stringify(data) });

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
  const params = new URLSearchParams();
  if (filters.page) params.set("page", String(filters.page));
  if (filters.per_page) params.set("per_page", String(filters.per_page));
  if (filters.min_score) params.set("min_score", String(filters.min_score));
  if (filters.status) params.set("status", filters.status);
  if (filters.source) params.set("source", filters.source);
  if (filters.search) params.set("search", filters.search);
  return fetchAPI(`/api/jobs/?${params}`);
};

export const bulkFeedback = (jobIds: number[], status: string) =>
  fetchAPI("/api/jobs/bulk/feedback", {
    method: "PATCH",
    body: JSON.stringify({ job_ids: jobIds, status }),
  });

export const getJob = (id: number) => fetchAPI(`/api/jobs/${id}`);

export const updateJobFeedback = (id: number, status: string, notes?: string) =>
  fetchAPI(`/api/jobs/${id}/feedback`, {
    method: "PATCH",
    body: JSON.stringify({ status, user_notes: notes }),
  });

// Export
export const exportJobsCSV = async (filters: JobFilters = {}) => {
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
  fetchAPI("/api/profile/", { method: "DELETE" });

// Billing
export const getBillingStatus = () => fetchAPI("/api/billing/status");
export const createCheckout = () =>
  fetchAPI("/api/billing/checkout", { method: "POST" });
export const createPortal = () =>
  fetchAPI("/api/billing/portal", { method: "POST" });

// Admin
export const getAdminUsers = () => fetchAPI("/api/admin/users");
export const getAdminScrapers = () => fetchAPI("/api/admin/scrapers");
export const getAdminMetrics = () => fetchAPI("/api/admin/metrics");

// Stats
export const getStats = () => fetchAPI("/api/stats/");

// Charts
export const getChartData = () => fetchAPI("/api/stats/charts");

// Scrape runs
export const getScrapeRuns = (limit = 10) =>
  fetchAPI(`/api/scrape-runs/?limit=${limit}`);
