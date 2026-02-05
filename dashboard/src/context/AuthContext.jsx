import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);

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
      // Also fetch subscription status
      fetchSubscription();
    } catch (err) {
      // Only clear user if it's actually an auth error
      if (err?.status === 401) {
        setUser(null);
        setSubscription(null);
      }
      // Network errors: keep current user state (don't log out on wifi hiccup)
    } finally {
      setLoading(false);
    }
  }, [fetchSubscription]);

  useEffect(() => {
    if (localStorage.getItem("access_token")) fetchUser();
    else setLoading(false);
  }, [fetchUser]);

  // Periodically refresh user data (every 30 min) to keep session alive
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(fetchUser, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, [user, fetchUser]);

  // Poll subscription status every 5 min (to detect expiry/renewal reminders)
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(fetchSubscription, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [user, fetchSubscription]);

  const login = (tokens) => {
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    fetchUser();
  };

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    setSubscription(null);
  };

  return (
    <AuthCtx.Provider value={{ user, subscription, loading, login, logout, refresh: fetchUser }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
