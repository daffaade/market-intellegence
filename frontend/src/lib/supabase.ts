import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined;

/**
 * Supabase client for sign-in and per-user data. null when the env vars are
 * missing, in which case the app runs without accounts (local-only data).
 * The publishable key is safe to ship: row-level security limits every row
 * to its owner.
 */
export const supabase: SupabaseClient | null =
  url && key
    ? createClient(url, key, {
        auth: { flowType: 'pkce', persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
      })
    : null;

export const authEnabled = supabase !== null;
