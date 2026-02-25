import { saveTokens, getAccessToken, getRefreshToken, clearTokens } from "./storage";

const BASE = import.meta.env.VITE_API_URL || "/api";

let isRefreshing = false;
let refreshQueue = [];

function onRefreshed(success) {
  refreshQueue.forEach((cb) => cb(success));
  refreshQueue = [];
}

// Returns { success, serverError }
// serverError=true → network/server issue → keep tokens, don't log user out
// serverError=false + success=false → refresh token 401 = genuinely invalid → clear tokens
async function tryRefresh() {
  const rt = getRefreshToken();
  if (!rt) {
    console.warn("[auth] tryRefresh: no refresh token in localStorage → logout");
    return { success: false, serverError: false };
  }
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (res.ok) {
      const data = await res.json();
      saveTokens(data.access_token, data.refresh_token);
      return { success: true, serverError: false };
    }
    // Only 401 = refresh token genuinely invalid/expired → logout user
    // Everything else (429 rate-limit, 400 bad request, 5xx crash) = keep session
    if (res.status === 401) {
      const errData = await res.json().catch(() => ({}));
      console.warn("[auth] tryRefresh: 401 from /auth/refresh →", errData?.error, "→ logout");
      return { success: false, serverError: false };
    }
    console.warn("[auth] tryRefresh: non-401 error", res.status, "→ keep session");
    return { success: false, serverError: true };
  } catch (err) {
    console.warn("[auth] tryRefresh: network error →", err, "→ keep session");
    return { success: false, serverError: true };
  }
}

async function request(path, opts = {}) {
  const token = getAccessToken();
  const headers = { "Content-Type": "application/json", ...opts.headers };
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${BASE}${path}`, { ...opts, headers });
  } catch (err) {
    throw { status: 0, error: "Sin conexión. Revisa tu internet." };
  }

  if (res.status === 401) {
    console.warn("[auth] 401 from", path, "→ attempting token refresh");
    // If already refreshing, wait for the result
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push((success) => {
          if (success) {
            resolve(request(path, opts));
          } else {
            // A new login may have saved fresh tokens while we waited
            const freshToken = getAccessToken();
            if (freshToken && freshToken !== token) {
              resolve(request(path, opts));
            } else {
              reject({ status: 401, error: "Sesión expirada" });
            }
          }
        });
      });
    }

    isRefreshing = true;
    const { success: refreshed, serverError } = await tryRefresh();
    isRefreshing = false;
    onRefreshed(refreshed);

    if (refreshed) return request(path, opts);

    // Only clear tokens if they haven't been replaced by a new login
    const currentToken = getAccessToken();
    if (currentToken && currentToken !== token) {
      // A new login saved fresh tokens during the refresh — retry
      return request(path, opts);
    }

    if (!serverError) {
      console.warn("[auth] Refresh failed with 401 → soft-expire (retry screen) for path:", path);
      // Don't clear tokens here — AuthContext.refresh() will do a confirmed hard-logout
      // if the tokens are genuinely invalid after the user clicks "Reconectarme".
      window.dispatchEvent(new CustomEvent("auth:logout"));
    } else {
      console.warn("[auth] Refresh failed with server error → keeping session for path:", path);
    }

    throw { status: 401, error: "Sesión expirada. Inicia sesión de nuevo." };
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, error: data.error || "Error del servidor", ...data };
  return data;
}

async function uploadRequest(path, formData) {
  const token = getAccessToken();
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  // No Content-Type header — browser sets multipart boundary automatically

  let res;
  try {
    res = await fetch(`${BASE}${path}`, { method: "POST", headers, body: formData });
  } catch (err) {
    throw { status: 0, error: "Sin conexión. Revisa tu internet." };
  }

  if (res.status === 401) {
    console.warn("[auth] 401 from upload", path, "→ attempting token refresh");
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push((success) => {
          if (success) {
            resolve(uploadRequest(path, formData));
          } else {
            const freshToken = getAccessToken();
            if (freshToken && freshToken !== token) {
              resolve(uploadRequest(path, formData));
            } else {
              reject({ status: 401, error: "Sesión expirada" });
            }
          }
        });
      });
    }
    isRefreshing = true;
    const { success: refreshed, serverError } = await tryRefresh();
    isRefreshing = false;
    onRefreshed(refreshed);
    if (refreshed) return uploadRequest(path, formData);

    const currentToken = getAccessToken();
    if (currentToken && currentToken !== token) {
      return uploadRequest(path, formData);
    }

    if (!serverError) {
      console.warn("[auth] Upload refresh failed → soft-expire for path:", path);
      window.dispatchEvent(new CustomEvent("auth:logout"));
    }

    throw { status: 401, error: "Sesión expirada. Inicia sesión de nuevo." };
  }

  const data = await res.json().catch(() => ({}));

  // Special handling for payment verification responses
  // 202 = Accepted (pending review) - return data, let caller handle
  // 422 = Unprocessable Entity (rejected but can retry) - include full data in error
  if (!res.ok) {
    throw {
      status: res.status,
      httpStatus: res.status,
      error: data.error || "Error del servidor",
      ...data,
    };
  }

  return data;
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: "PUT", body: JSON.stringify(body) }),
  del: (path) => request(path, { method: "DELETE" }),
  upload: (path, formData) => uploadRequest(path, formData),
};
