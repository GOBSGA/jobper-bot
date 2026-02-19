import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { saveTokens, getAccessToken, clearTokens } from "../lib/storage";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  // serverError: true when /user/profile returned 5xx/network — not a logout, just a server issue
  const [serverError, setServerError] = useState(false);

  const fetchSubscription = useCallback(async () => {
    try {
      const data = await api.get("/payments/subscription");
      setSubscription(data?.subscription || null);
    } catch {
      // Non-critical — don't clear subscription on network errors
    }
  }, []);

  const fetchUser = useCallback(async () => {
    try {
      const data = await api.get("/user/profile");
      setUser(data);
      setServerError(false);
      // Also fetch subscription status
      fetchSubscription();
    } catch (err) {
      if (err?.status === 401) {
        // Genuine auth failure — clear session
        setUser(null);
        setSubscription(null);
        setServerError(false);
      } else {
        // Server/network error — don't clear existing user data, just flag it
        setServerError(true);
      }
      // Re-throw so login page can handle errors (e.g., show "wrong password")
      // BUT only for 401 — server errors on background polls should not propagate
      if (err?.status === 401) throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchSubscription]);

  useEffect(() => {
    if (getAccessToken()) {
      fetchUser().catch(() => {
        // Suppress unhandled rejection — non-401 errors are handled inside fetchUser
      });
    } else {
      setLoading(false);
    }
  }, [fetchUser]);

  // Periodically refresh user data (every 30 min) to keep session alive
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      fetchUser().catch(() => {}); // Suppress background poll errors
    }, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, [user, fetchUser]);

  // Poll subscription status every 5 min (to detect expiry/renewal reminders)
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(fetchSubscription, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [user, fetchSubscription]);

  // Sync auth state across tabs (login/logout in one tab reflects in others)
  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === "access_token") {
        if (!e.newValue) {
          // Token removed in another tab (logout)
          setUser(null);
          setSubscription(null);
        } else if (e.newValue !== e.oldValue) {
          // Token updated in another tab (login or refresh)
          fetchUser().catch(() => {});
        }
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [fetchUser]);

  const login = async (tokens) => {
    saveTokens(tokens.access_token, tokens.refresh_token);
    setServerError(false);
    // Login response already contains user — use it directly to avoid a second
    // API call that could fail and make login appear broken.
    if (tokens.user) {
      setUser(tokens.user);
      setLoading(false);
      fetchSubscription(); // non-blocking, non-critical
    } else {
      setLoading(true);
      await fetchUser();
    }
  };

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    clearTokens();
    setUser(null);
    setSubscription(null);
    setServerError(false);
  };

  return (
    <AuthCtx.Provider value={{ user, subscription, loading, serverError, login, logout, refresh: fetchUser }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
