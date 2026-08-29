import axios from "axios";
import { clearAccessToken, clearCurrentUser, clearRefreshToken, getAccessToken, getRefreshToken, setAccessToken, setCurrentUser, setRefreshToken } from "./session";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/",
  withCredentials: false,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Safe reauthentication: an expired access token (60 min) must never dead-end
// a live clinical screen (e.g. mid visit-recording) with a raw 401. On a 401
// from any request other than the refresh call itself, exchange the stored
// refresh token for a new access token and silently retry the original
// request once. Concurrent 401s share a single in-flight refresh call so we
// never hammer /auth/refresh. If there is no refresh token, or the refresh
// call itself fails (expired/revoked/user deactivated), clear the session
// and send the user back to /login -- never a silent auto-relogin with a
// stored password, and never an infinite retry loop.
let refreshPromise: Promise<string | null> | null = null;

function redirectToLogin() {
  clearAccessToken();
  clearRefreshToken();
  clearCurrentUser();
  if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
    window.location.href = "/login";
  }
}

async function performRefresh(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;
  try {
    const base = import.meta.env.VITE_API_BASE_URL ?? "";
    const response = await axios.post(`${base}/auth/refresh`, { refresh_token: refreshToken });
    const data = response.data as { access_token: string; refresh_token: string; user: unknown };
    setAccessToken(data.access_token);
    setRefreshToken(data.refresh_token);
    if (data.user) setCurrentUser(data.user as Parameters<typeof setCurrentUser>[0]);
    return data.access_token;
  } catch {
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error?.config;
    const status = error?.response?.status;
    const url: string = originalRequest?.url || "";

    if (status !== 401 || !originalRequest || url.includes("/auth/refresh") || url.includes("/auth/login")) {
      return Promise.reject(error);
    }

    if (originalRequest._retriedAfterRefresh) {
      redirectToLogin();
      return Promise.reject(error);
    }
    originalRequest._retriedAfterRefresh = true;

    if (!refreshPromise) {
      refreshPromise = performRefresh().finally(() => {
        refreshPromise = null;
      });
    }
    const newAccessToken = await refreshPromise;

    if (!newAccessToken) {
      redirectToLogin();
      return Promise.reject(error);
    }

    // Don't hand-patch the Authorization header on originalRequest.headers here --
    // axios's AxiosHeaders wrapper can retain the stale value from the failed
    // first attempt even after a plain property assignment/delete, causing the
    // retry to silently resend the same expired token and 401 again. Replace
    // the whole headers object with a fresh plain object and let the request
    // interceptor (which always reads the just-updated token fresh from
    // storage) populate it correctly on the retry.
    originalRequest.headers = { "Content-Type": "application/json" };
    return api(originalRequest);
  }
);

export default api;
