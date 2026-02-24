import { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { api } from "../lib/api";
import { saveTokens, getAccessToken, saveUser, getUser, clearAll } from "../lib/storage";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  // Initialize synchronously from localStorage — zero loading flash when session exists
  const [user, setUserState] = useState(() => (getAccessToken() ? getUser() : null));
  const [subscription, setSubscription] = useState(null);
  // Show loading only if we have a token but no cached user (must wait for network)
  const [loading, setLoading] = useState(() => Boolean(getAccessToken() && !getUser()));
  const [serverError, setServerError] = useState(false);

  // isLoggedIn ref: set false on logout/401 so stale in-flight fetches become no-ops
  const isLoggedIn = useRef(Boolean(getAccessToken()));

  const fetchSubscription = useCallback(async () => {
    try {
      const data = await api.get("/payments/subscription");
      setSubscription(data?.subscription || null);
    } catch {}
  }, []);

  const fetchUser = useCallback(async () => {
    try {
      const data = await api.get("/user/profile");
      if (!isLoggedIn.current) return; // logged out while fetching — discard
      saveUser(data);
      setUserState(data);
      setServerError(false);
      fetchSubscription();
    } catch (err) {
      if (!isLoggedIn.current) return; // logged out while fetching — discard
      if (err?.status === 401) {
        isLoggedIn.current = false;
        clearAll();
        setUserState(null);
        setSubscription(null);
        setServerError(false);
      } else {
        // Network/server error — keep existing cached user, just flag it
        setServerError(true);
      }
    } finally {
      setLoading(false);
    }
  }, [fetchSubscription]);

  // On mount: validate token in background (user is already shown from cache)
  useEffect(() => {
    if (getAccessToken()) {
      fetchUser().catch(() => setLoading(false));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Poll subscription status every 5 min
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(fetchSubscription, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [user, fetchSubscription]);

  // Sync logout/login across browser tabs
  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === "access_token") {
        if (!e.newValue) {
          isLoggedIn.current = false;
          setUserState(null);
          setSubscription(null);
        } else if (e.newValue !== e.oldValue) {
          isLoggedIn.current = true;
          fetchUser().catch(() => {});
        }
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [fetchUser]);

  const login = async (tokens) => {
    isLoggedIn.current = true;
    saveTokens(tokens.access_token, tokens.refresh_token);
    setServerError(false);

    if (tokens.user) {
      // Login response always includes user — use directly, no extra API call needed
      saveUser(tokens.user);
      setUserState(tokens.user);
      setLoading(false);
      if (!tokens.user.needs_privacy_acceptance) {
        fetchSubscription();
      }
    } else {
      setLoading(true);
      await fetchUser();
    }
  };

  const logout = async () => {
    isLoggedIn.current = false;
    try { await api.post("/auth/logout"); } catch {}
    clearAll();
    setUserState(null);
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
