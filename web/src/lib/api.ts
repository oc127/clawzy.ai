const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

// --- Token refresh logic ---
let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

async function tryRefreshToken(): Promise<boolean> {
  const refreshToken =
    typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  // Auto-refresh on 401
  if (res.status === 401 && token) {
    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = tryRefreshToken().then((ok) => {
        isRefreshing = false;
        if (!ok) {
          localStorage.removeItem("token");
          localStorage.removeItem("refresh_token");
          if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
            window.location.href = "/login";
          }
        }
      });
    }
    await refreshPromise;

    // Retry with new token
    const newToken = localStorage.getItem("token");
    if (newToken && newToken !== token) {
      const retry = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${newToken}`,
          ...options.headers,
        },
      });
      if (!retry.ok) {
        const body = await retry.json().catch(() => ({}));
        throw new ApiError(retry.status, body.detail || "Request failed");
      }
      return retry.json();
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail || "Request failed");
  }

  // Handle 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json();
}

// --- Auth ---
export async function register(email: string, password: string, name: string) {
  return request<{ access_token: string; refresh_token: string }>(
    "/auth/register",
    { method: "POST", body: JSON.stringify({ email, password, name }) }
  );
}

export async function login(email: string, password: string) {
  return request<{ access_token: string; refresh_token: string }>(
    "/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) }
  );
}

export async function forgotPassword(email: string) {
  return request<{ message: string }>("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(token: string, newPassword: string) {
  return request<{ message: string }>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export async function verifyEmail(token: string) {
  return request<{ message: string }>("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

// --- User ---
export async function getMe() {
  return request<{
    id: string;
    email: string;
    name: string;
    credit_balance: number;
    email_verified: boolean;
  }>("/users/me");
}

export async function updateMe(data: { name?: string }) {
  return request<{ id: string; name: string; email: string }>("/users/me", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function changePassword(currentPassword: string, newPassword: string) {
  return request<{ message: string }>("/users/me/change-password", {
    method: "POST",
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}

// --- Agents ---
export interface Agent {
  id: string;
  name: string;
  model_name: string;
  status: "creating" | "running" | "stopped" | "error";
  ws_port: number | null;
  created_at: string;
}

export async function listAgents() {
  return request<Agent[]>("/agents");
}

export async function createAgent(name: string, model_name: string) {
  return request<Agent>("/agents", {
    method: "POST",
    body: JSON.stringify({ name, model_name }),
  });
}

export async function deleteAgent(id: string) {
  return request<void>(`/agents/${id}`, { method: "DELETE" });
}

export async function startAgent(id: string) {
  return request<Agent>(`/agents/${id}/start`, { method: "POST" });
}

export async function stopAgent(id: string) {
  return request<Agent>(`/agents/${id}/stop`, { method: "POST" });
}

export async function createCheckoutSession(priceId: string) {
  return request<{ url: string }>(
    `/billing/checkout?price_id=${encodeURIComponent(priceId)}`,
    { method: "POST" }
  );
}

// --- Models ---
export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  tier: string;
  credits_per_1k_input: number;
  credits_per_1k_output: number;
  description: string;
}

export async function listModels() {
  return request<{ models: ModelInfo[] }>("/models");
}

// --- Billing ---
export interface CreditsInfo {
  balance: number;
  used_this_period: number;
  plan: string;
}

export async function getCredits() {
  return request<CreditsInfo>("/billing/credits");
}

export async function getPlans() {
  return request<
    { id: string; name: string; price_monthly: number; credits_included: number; max_agents: number }[]
  >("/billing/plans");
}

export { ApiError };
