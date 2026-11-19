import axios from "axios";

export const ACCESS_KEY = "sunstay_access_token";
export const REFRESH_KEY = "sunstay_refresh_token";
export const USER_KEY = "sunstay_user";

const API_BASE = import.meta.env.VITE_API_URL || "/api";
const ANALYTICS_BASE = import.meta.env.VITE_ANALYTICS_URL || "/analytics/api";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

export const analyticsApi = axios.create({
  baseURL: ANALYTICS_BASE,
  timeout: 120000,
});

for (const client of [api, analyticsApi]) {
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem(ACCESS_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
}

// Разогрев Render free: первый запрос может занять до минуты.
api.get("/health").catch(() => {});
analyticsApi.get("/openapi.json").catch(() => {});

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg ?? String(item)).join("; ");
    }
    if (error.message) return error.message;
  }
  return "Что-то пошло не так";
}

export async function downloadFile(
  client: typeof api,
  url: string,
  filename: string,
  params?: Record<string, unknown>,
) {
  const response = await client.get(url, {
    params,
    responseType: "blob",
  });
  const blobUrl = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(blobUrl);
}
