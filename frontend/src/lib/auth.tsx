import React, { createContext, useContext, useEffect, useState } from 'react';
import type { Session, User } from '@supabase/supabase-js';
import { supabase } from './supabase';

interface AuthState {
  /** false until the stored session (or the OAuth redirect code) has been read. */
  ready: boolean;
  session: Session | null;
  user: User | null;
  signInWithGoogle: () => Promise<string | null>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [ready, setReady] = useState(!supabase);
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setReady(true);
    });
    const { data } = supabase.auth.onAuthStateChange((_event, s) => setSession(s));
    return () => data.subscription.unsubscribe();
  }, []);

  const signInWithGoogle = async (): Promise<string | null> => {
    if (!supabase) return 'Login belum dikonfigurasi.';
    // Return to the same page (and hash route) after Google; the first
    // sign-in creates the account, so this is also the sign-up flow.
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin + window.location.pathname + window.location.hash }
    });
    return error ? error.message : null;
  };

  const signOut = async () => {
    await supabase?.auth.signOut();
  };

  return (
    <AuthContext.Provider value={{ ready, session, user: session?.user ?? null, signInWithGoogle, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthState => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
};

/** Display name and avatar from the Google profile Supabase stores in user_metadata. */
export const profileOf = (user: User) => {
  const m = user.user_metadata ?? {};
  const name: string = m.full_name || m.name || user.email || 'Pengguna';
  return { name, email: user.email ?? '', avatar: (m.avatar_url || m.picture || '') as string };
};
