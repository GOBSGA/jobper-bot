/**
 * Centralized localStorage token management
 * Single source of truth for auth token storage
 */

const KEYS = {
  ACCESS_TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
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
