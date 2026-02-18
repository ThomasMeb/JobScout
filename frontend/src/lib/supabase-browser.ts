import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | null = null;

export function createClient(): SupabaseClient {
  if (client) return client;

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

  // During SSR/build without env vars, provide placeholders
  // The real client is only useful in the browser
  client = createBrowserClient(url || "https://placeholder.supabase.co", key || "placeholder");
  return client;
}
