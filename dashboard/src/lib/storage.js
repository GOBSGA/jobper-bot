/**
 * Centralized localStorage token + user management
 * Single source of truth for auth storage
 */

const KEYS = {
  ACCESS_TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
  USER: "auth_user",
};

export const saveTokens = (accessToken, refreshToken) => {
  localStorage.setItem(KEYS.ACCESS_TOKEN, accessToken);
  localStorage.setItem(KEYS.REFRESH_TOKEN, refreshToken);
};

export const getAccessToken = () => localStorage.getItem(KEYS.ACCESS_TOKEN);

export const getRefreshToken = () => localStorage.getItem(KEYS.REFRESH_TOKEN);

export const clearTokens = () => {
  localStorage.removeItem(KEYS.ACCESS_TOKEN);
  localStorage.removeItem(KEYS.REFRESH_TOKEN);
};

export const saveUser = (user) => {
  try {
    localStorage.setItem(KEYS.USER, JSON.stringify(user));
  } catch {}
};

export const getUser = () => {
  try {
    const raw = localStorage.getItem(KEYS.USER);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export const clearUser = () => {
  localStorage.removeItem(KEYS.USER);
};

/** Clears tokens + cached user atomically (use on logout or 401) */
export const clearAll = () => {
  localStorage.removeItem(KEYS.ACCESS_TOKEN);
  localStorage.removeItem(KEYS.REFRESH_TOKEN);
  localStorage.removeItem(KEYS.USER);
};
