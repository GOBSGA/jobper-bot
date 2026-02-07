const BASE = import.meta.env.VITE_API_URL || "/api";

let isRefreshing = false;
let refreshQueue = [];

function onRefreshed(success) {
  refreshQueue.forEach((cb) => cb(success));
  refreshQueue = [];
}

async function request(path, opts = {}) {
  const token = localStorage.getItem("access_token");
  const headers = { "Content-Type": "application/json", ...opts.headers };
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${BASE}${path}`, { ...opts, headers });
  } catch (err) {
    throw { status: 0, error: "Sin conexión. Revisa tu internet." };
  }

  if (res.status === 401) {
    // If already refreshing, wait for the result
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push((success) => {
          if (success) resolve(request(path, opts));
          else reject({ status: 401, error: "Sesión expirada" });
        });
      });
    }

    isRefreshing = true;
    const refreshed = await tryRefresh();
    isRefreshing = false;
    onRefreshed(refreshed);

    if (refreshed) return request(path, opts);

    // Don't hard redirect — let AuthContext handle it
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    throw { status: 401, error: "Sesión expirada. Inicia sesión de nuevo." };
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, error: data.error || "Error del servidor", ...data };
  return data;
}

async function tryRefresh() {
  const rt = localStorage.getItem("refresh_token");
  if (!rt) return false;
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

async function uploadRequest(path, formData) {
  const token = localStorage.getItem("access_token");
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
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push((success) => {
          if (success) resolve(uploadRequest(path, formData));
          else reject({ status: 401, error: "Sesión expirada" });
        });
      });
    }
    isRefreshing = true;
    const refreshed = await tryRefresh();
    isRefreshing = false;
    onRefreshed(refreshed);
    if (refreshed) return uploadRequest(path, formData);

    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
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
