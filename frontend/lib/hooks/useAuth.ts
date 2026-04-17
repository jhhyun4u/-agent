"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import type { User } from "@supabase/supabase-js";

export interface UseAuthReturn {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: Error | null;
  isAuthenticated: boolean;
}

/**
 * Get current authenticated user and JWT token from Supabase session
 */
export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const supabase = createClient();

    const getSession = async () => {
      try {
        setIsLoading(true);
        const {
          data: { session },
          error: err,
        } = await supabase.auth.getSession();

        if (err) {
          setError(err as Error);
          setUser(null);
          setToken(null);
          return;
        }

        if (session?.user) {
          setUser(session.user);
          setToken(session.access_token || null);
          setError(null);
        } else {
          setUser(null);
          setToken(null);
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    getSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (session?.user) {
        setUser(session.user);
        setToken(session.access_token || null);
        setError(null);
      } else {
        setUser(null);
        setToken(null);
      }
    });

    return () => {
      subscription?.unsubscribe();
    };
  }, []);

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated: user !== null && token !== null,
  };
}
