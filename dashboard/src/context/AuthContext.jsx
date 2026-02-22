import { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { api } from "../lib/api";
import { saveTokens, getAccessToken, clearTokens } from "../lib/storage";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  // serverError: true when /user/profile returned 5xx/network — not a logout, just a server issue
  const [serverError, setServerError] = useState(false);

  // Auth version counter: incremented on every login/logout.
  // Any in-flight fetchUser that started before the version change
  // will silently discard its results, preventing race conditions.
  const authVersion = useRef(0);

  const fetchSubscription = useCallback(async () => {
    try {
      const data = await api.get("/payments/subscription");
      setSubscription(data?.subscription || null);
    } catch {
      // Non-critical — don't clear subscription on network errors
    }
  }, []);

  const fetchUser = useCallback(async () => {
    const myVersion = authVersion.current;
    try {
      const data = await api.get("/user/profile");
      // Discard result if a login/logout happened while we were fetching
      if (authVersion.current !== myVersion) return;
      setUser(data);
      setServerError(false);
      fetchSubscription();
    } catch (err) {
      // Discard error if a login/logout happened while we were fetching
      if (authVersion.current !== myVersion) return;

      if (err?.status === 401) {
        setUser(null);
        setSubscription(null);
        setServerError(false);
      } else {
        // Server/network error — don't clear existing user data, just flag it
        setServerError(true);
      }
      // Re-throw 401 only if there's genuinely no token (not a stale-token scenario)
      if (err?.status === 401 && !getAccessToken()) throw err;
    } finally {
      if (authVersion.current === myVersion) {
        setLoading(false);
      }
    }
  }, [fetchSubscription]);

  // On mount: restore session from stored token
  useEffect(() => {
    if (getAccessToken()) {
      fetchUser().catch(() => {});
    } else {
      setLoading(false);
    }
  }, [fetchUser]);

  // Periodically refresh user data (every 30 min) to keep session alive
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      fetchUser().catch(() => {});
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
          authVersion.current += 1;
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
    // Bump version FIRST — invalidates any in-flight fetchUser so it
    // can never overwrite or clear the fresh login state
    authVersion.current += 1;

    saveTokens(tokens.access_token, tokens.refresh_token);
    setServerError(false);

    if (tokens.user) {
      // Login response includes user data — use directly (no extra API call)
      setUser(tokens.user);
      setLoading(false);
      // Skip subscription fetch if privacy acceptance is pending
      if (!tokens.user.needs_privacy_acceptance) {
        fetchSubscription();
      }
    } else {
      // Fallback: fetch user profile (e.g., token-only response)
      setLoading(true);
      await fetchUser();
    }
  };

  const logout = async () => {
    // Bump version to cancel any in-flight operations
    authVersion.current += 1;

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
