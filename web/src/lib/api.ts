const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
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

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail || "Request failed");
  }

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

// --- User ---
export async function getMe() {
  return request<{
    id: string;
    email: string;
    name: string;
    credit_balance: number;
  }>("/users/me");
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
