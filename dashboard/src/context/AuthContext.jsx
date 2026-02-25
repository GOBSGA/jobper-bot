/**
 * AuthContext — event-driven auth, zero background polling.
 *
 * User state is set ONLY by:
 *   1. login() — from the login API response (synchronous, no extra round-trip)
 *   2. refresh() — explicit user-initiated refresh (e.g. after accepting privacy policy)
 *
 * User state is cleared ONLY by:
 *   1. logout() — explicit logout button
 *   2. "auth:logout" custom event — fired by api.js when refresh token is genuinely invalid
 *   3. storage event — another tab logged out
 *
 * This means there is NO background fetch that can race with login and clear the user.
 */
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { saveTokens, getAccessToken, saveUser, getUser, clearAll } from "../lib/storage";

const BASE = import.meta.env.VITE_API_URL || "/api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  // Initialize synchronously — zero loading flash
  const [user, setUserState] = useState(() => (getAccessToken() ? getUser() : null));
  const [subscription, setSubscription] = useState(null);
  const [loading] = useState(false); // never blocks rendering — no background fetch
  const [serverError, setServerError] = useState(false);

  const doLogout = useCallback(() => {
    console.warn("[auth] doLogout() called — trace:", new Error().stack?.split("\n").slice(1, 4).join(" | "));
    clearAll();
    setUserState(null);
    setSubscription(null);
    setServerError(false);
  }, []);

  // Uses raw fetch (NOT api.js) so a subscription endpoint failure can never
  // trigger auth:logout and expel the user. Errors are silently ignored.
  const fetchSubscription = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    try {
      const res = await fetch(`${BASE}/payments/subscription`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json().catch(() => null);
      setSubscription(data?.subscription || null);
    } catch {}
  }, []);

  // api.js dispatches this when the refresh token is invalid (same-tab communication)
  // Note: localStorage removeItem does NOT fire the storage event in the same tab,
  // so we use a custom event instead.
  useEffect(() => {
    window.addEventListener("auth:logout", doLogout);
    return () => window.removeEventListener("auth:logout", doLogout);
  }, [doLogout]);

  // Cross-tab sync: logout or login in another browser tab
  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === "access_token") {
        if (!e.newValue) {
          doLogout();
        } else if (e.newValue !== e.oldValue) {
          // Other tab logged in — pick up their cached user
          setUserState(getUser());
        }
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [doLogout]);

  // Poll subscription every 5 min while logged in
  useEffect(() => {
    if (!user?.id) return;
    const interval = setInterval(fetchSubscription, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [user?.id, fetchSubscription]);

  const login = async (tokens) => {
    saveTokens(tokens.access_token, tokens.refresh_token);
    setServerError(false);
    if (tokens.user) {
      saveUser(tokens.user);
      setUserState(tokens.user);
      if (!tokens.user.needs_privacy_acceptance) {
        fetchSubscription();
      }
    }
  };

  // Optimistic local update — use after accepting privacy policy to avoid logout risk
  const setUser = useCallback((updatedUser) => {
    saveUser(updatedUser);
    setUserState(updatedUser);
  }, []);

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    doLogout();
  };

  // Explicit refresh — call after accepting privacy policy or after plan change
  const refresh = useCallback(async () => {
    try {
      const data = await api.get("/user/profile");
      saveUser(data);
      setUserState(data);
      setServerError(false);
      fetchSubscription();
    } catch (err) {
      if (err?.status === 401) {
        doLogout();
      } else {
        setServerError(true);
      }
    }
  }, [fetchSubscription, doLogout]);

  return (
    <AuthCtx.Provider value={{ user, subscription, loading, serverError, login, logout, refresh, setUser }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
