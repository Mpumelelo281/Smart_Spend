import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const STORAGE_KEY = "smartspend.tokens";

export function getTokens() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setTokens(tokens) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
}

export function clearTokens() {
  localStorage.removeItem(STORAGE_KEY);
}

export const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const tokens = getTokens();
  if (tokens?.access) {
    config.headers.Authorization = `Bearer ${tokens.access}`;
  }
  return config;
});

// A single silent refresh-and-retry, matching the 15-minute access token
// lifetime configured server-side — the student never has to notice.
let refreshInFlight = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const tokens = getTokens();

    if (error.response?.status !== 401 || original._retried || !tokens?.refresh) {
      throw error;
    }
    original._retried = true;

    try {
      refreshInFlight =
        refreshInFlight ||
        axios.post(`${BASE_URL}/auth/token/refresh/`, { refresh: tokens.refresh }).finally(() => {
          refreshInFlight = null;
        });
      const { data } = await refreshInFlight;
      setTokens({ ...tokens, access: data.access });
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch (refreshError) {
      clearTokens();
      throw refreshError;
    }
  }
);
