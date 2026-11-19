const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";
const TOKEN_KEY = "facultyinsight.token";
const USER_KEY = "facultyinsight.user";

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getStoredUser<T>(): T | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function setStoredUser(user: unknown | null) {
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  else localStorage.removeItem(USER_KEY);
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  raw?: boolean;
}

export async function api<T = unknown>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, raw, headers, ...rest } = options;
  const token = getToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && token) {
    window.dispatchEvent(new CustomEvent("facultyinsight:unauthorized"));
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status}).`;
    let details: unknown;
    try {
      const payload = await response.json();
      details = payload;
      if (Array.isArray(payload.errors) && payload.errors.length) {
        detail = payload.errors
          .map((item: { field?: string; message?: string }) =>
            item.field ? `${item.field}: ${item.message}` : item.message,
          )
          .join(" ");
      } else if (typeof payload.detail === "string") {
        detail = payload.detail;
      }
    } catch {
      // Keep the generic message when the body is not JSON.
    }
    throw new ApiError(detail, response.status, details);
  }

  if (raw) return response as unknown as T;
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function downloadReport(
  path: string,
  format: "csv" | "pdf",
  fallbackName: string,
) {
  const response = await api<Response>(`${path}${path.includes("?") ? "&" : "?"}format=${format}`, {
    raw: true,
  });
  const blob = await response.blob();
  const disposition = response.headers.get("content-disposition") || "";
  const match = /filename\*=UTF-8''([^;]+)/i.exec(disposition);
  const filename = match ? decodeURIComponent(match[1]) : fallbackName;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
