import Constants from "expo-constants";
import { getAccessToken, clearTokens } from "./storage";
import { router } from "expo-router";

/** Dev: set `extra.apiBaseUrl` in app.json to your backend LAN IP (same Wi‑Fi as the phone/simulator Mac). */
function getApiBase(): string {
  if (!__DEV__) return "https://www.nipponclaw.com/api/v1";
  const fromConfig = Constants.expoConfig?.extra?.apiBaseUrl as string | undefined;
  if (fromConfig?.startsWith("http")) return fromConfig.replace(/\/$/, "");
  return "http://192.168.2.172/api/v1";
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

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
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

  if (res.status === 401) {
    await clearTokens();
    router.replace("/(auth)/login");
    throw new ApiError(401, "Unauthorized");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    const detail = body.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ")
          : "Request failed";
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
export interface Agent {
  id: string;
  name: string;
  description: string;
  model: string;
  status: "running" | "stopped" | "error";
  created_at: string;
  message_count?: number;
}
export interface AgentCreate {
  name: string;
  description?: string;
  model: string;
  system_prompt?: string;
}
export const getAgents = () => apiGet<Agent[]>("/agents");
export const getAgent = (id: string) => apiGet<Agent>(`/agents/${id}`);
export const createAgent = (data: AgentCreate) => apiPost<Agent>("/agents", data);
export const deleteAgent = (id: string) => apiDelete(`/agents/${id}`);

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
export interface Model {
  id: string;
  name: string;
  provider: string;
  description: string;
  context_length: number;
  cost_per_1k_tokens: number;
  tier: "free" | "starter" | "pro";
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
