import Constants from "expo-constants";
import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from "./storage";
import { router } from "expo-router";

/** Dev: set `extra.apiBaseUrl` in app.json to your backend LAN IP (same Wi‑Fi as the phone/simulator Mac). */
export function getApiBase(): string {
  if (!__DEV__) return "https://www.nipponclaw.com/api/v1";
  const fromConfig = Constants.expoConfig?.extra?.apiBaseUrl as string | undefined;
  if (fromConfig?.startsWith("http")) return fromConfig.replace(/\/$/, "");
  return "http://192.168.2.172/api/v1";
}

/** Returns the origin (scheme + host) without the /api/v1 path. */
export function getApiHost(): string {
  const base = getApiBase();
  const idx = base.indexOf("/api/v1");
  return idx !== -1 ? base.slice(0, idx) : base;
}

const API_BASE = getApiBase();

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
  }
}

/** Prevent concurrent refresh requests */
let refreshPromise: Promise<boolean> | null = null;

async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken) return false;
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    await saveTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

async function request<T>(path: string, options: RequestInit = {}, _isRetry = false): Promise<T> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch (e) {
    const hint =
      "无法连接服务器。请在 mobile/app.json 的 expo.extra.apiBaseUrl 填你后端电脑的局域网 IP（例如 http://192.168.x.x/api/v1），手机和电脑要同一 Wi‑Fi。";
    const msg = e instanceof Error ? e.message : String(e);
    throw new ApiError(0, `${hint}\n(${msg})`);
  }

  async function parseErrorBody(): Promise<string> {
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail))
      return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ") || "Request failed";
    return "Request failed";
  }

  if (res.status === 401) {
    const isAuthForm = path === "/auth/login" || path === "/auth/register";
    if (!isAuthForm && !_isRetry) {
      // Try refreshing the token before giving up
      if (!refreshPromise) {
        refreshPromise = tryRefreshToken().finally(() => { refreshPromise = null; });
      }
      const refreshed = await refreshPromise;
      if (refreshed) {
        return request<T>(path, options, true);
      }
    }
    const msg = await parseErrorBody();
    if (!isAuthForm) {
      await clearTokens();
      router.replace("/(auth)/login");
    }
    throw new ApiError(401, msg || "Unauthorized");
  }

  if (!res.ok) {
    const msg = await parseErrorBody();
    throw new ApiError(res.status, msg || "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const apiGet = <T>(path: string) => request<T>(path);
export const apiPost = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
export const apiPatch = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined });
export const apiDelete = (path: string) =>
  request<void>(path, { method: "DELETE" });

// ── Auth ──────────────────────────────────────────────────────────────────────
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
export const loginApi = (email: string, password: string) =>
  apiPost<LoginResponse>("/auth/login", { email, password });
export const registerApi = (email: string, password: string, name: string) =>
  apiPost<LoginResponse>("/auth/register", { email, password, name });

// ── User ──────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  name: string;
  credit_balance: number;
  plan: string;
  created_at: string;
}
export const getMe = () => apiGet<User>("/users/me");

// ── Agents ────────────────────────────────────────────────────────────────────
/** Matches backend AgentResponse */
export interface Agent {
  id: string;
  name: string;
  model_name: string;
  status: string;
  created_at: string;
  ws_port?: number | null;
  last_active_at?: string | null;
}
export interface AgentCreate {
  name: string;
  model_name: string;
}
export const getAgents = () => apiGet<Agent[]>("/agents");
export const getAgent = (id: string) => apiGet<Agent>(`/agents/${id}`);
export const createAgent = (data: AgentCreate) => apiPost<Agent>("/agents", data);
export const updateAgent = (id: string, data: { name?: string; model_name?: string }) =>
  apiPatch<Agent>(`/agents/${id}`, data);
export const deleteAgent = (id: string) => apiDelete(`/agents/${id}`);
export const startAgent = (id: string) => apiPost<Agent>(`/agents/${id}/start`);
export const stopAgent = (id: string) => apiPost<Agent>(`/agents/${id}/stop`);
export const restartAgent = (id: string) => apiPost<Agent>(`/agents/${id}/restart`);

// ── Chat ──────────────────────────────────────────────────────────────────────
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}
export interface Conversation {
  id: string;
  agent_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}
export const getConversations = (agentId: string) =>
  apiGet<Conversation[]>(`/agents/${agentId}/conversations`);
export const getMessages = (agentId: string, convId: string) =>
  apiGet<Message[]>(`/agents/${agentId}/conversations/${convId}/messages`);
export const createConversation = (agentId: string) =>
  apiPost<Conversation>(`/agents/${agentId}/conversations`);

// ── Models ────────────────────────────────────────────────────────────────────
/** Matches backend ModelInfo */
export interface Model {
  id: string;
  name: string;
  provider: string;
  description: string;
  tier: string;
  credits_per_1k_input: number;
  credits_per_1k_output: number;
}
export const getModels = () => apiGet<Model[]>("/models");

// ── Billing ───────────────────────────────────────────────────────────────────
export interface CreditTransaction {
  id: string;
  amount: number;
  type: "usage" | "purchase" | "bonus";
  description: string;
  created_at: string;
}
export const getTransactions = () =>
  apiGet<CreditTransaction[]>("/billing/transactions");
