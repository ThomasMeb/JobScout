const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    throw new Error(error.detail || "API error");
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
}

export const getJobs = (filters: JobFilters = {}) => {
  const params = new URLSearchParams();
  if (filters.page) params.set("page", String(filters.page));
  if (filters.per_page) params.set("per_page", String(filters.per_page));
  if (filters.min_score) params.set("min_score", String(filters.min_score));
  if (filters.status) params.set("status", filters.status);
  if (filters.source) params.set("source", filters.source);
  return fetchAPI(`/api/jobs/?${params}`);
};

export const getJob = (id: number) => fetchAPI(`/api/jobs/${id}`);

export const updateJobFeedback = (id: number, status: string, notes?: string) =>
  fetchAPI(`/api/jobs/${id}/feedback`, {
    method: "PATCH",
    body: JSON.stringify({ status, user_notes: notes }),
  });

// Stats
export const getStats = () => fetchAPI("/api/stats/");
