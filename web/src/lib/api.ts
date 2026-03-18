import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from "./auth";

const API_BASE = "/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
  }
}

// Prevent multiple concurrent token refreshes
let refreshPromise: Promise<boolean> | null = null;
// Prevent multiple concurrent 401 redirects
let isRedirecting = false;

async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    saveTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    // Try to refresh token (deduplicate concurrent refreshes)
    if (!refreshPromise) {
      refreshPromise = tryRefreshToken().finally(() => {
        refreshPromise = null;
      });
    }
    const refreshed = await refreshPromise;

    if (refreshed) {
      // Retry the original request with new token
      const newToken = getAccessToken();
      if (newToken) {
        headers["Authorization"] = `Bearer ${newToken}`;
      }
      const retryRes = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
      });
      if (retryRes.ok) {
        if (retryRes.status === 204) return undefined as T;
        return retryRes.json();
      }
    }

    // Refresh failed — redirect to login (only once)
    clearTokens();
    if (typeof window !== "undefined" && !isRedirecting) {
      isRedirecting = true;
      window.location.href = "/login";
    }
    throw new ApiError(401, "Unauthorized");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(res.status, body.detail || "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "PATCH",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function apiDelete(path: string): Promise<void> {
  return request<void>(path, { method: "DELETE" });
}

// --- Integrations API ---

import type { Integration } from "./types";

export function getIntegrations(agentId: string): Promise<Integration[]> {
  return apiGet<Integration[]>(`/integrations/agents/${agentId}`);
}

export function createIntegration(
  agentId: string,
  data: {
    platform: string;
    bot_token?: string;
    channel_secret?: string;
    channel_access_token?: string;
  },
): Promise<Integration> {
  return apiPost<Integration>(`/integrations/agents/${agentId}`, data);
}

export function updateIntegration(
  integrationId: string,
  data: {
    bot_token?: string;
    channel_secret?: string;
    channel_access_token?: string;
    enabled?: boolean;
  },
): Promise<Integration> {
  return apiPatch<Integration>(`/integrations/${integrationId}`, data);
}

export function deleteIntegration(integrationId: string): Promise<void> {
  return apiDelete(`/integrations/${integrationId}`);
}

// --- Skills / ClawHub API ---

import type { SkillBrief, Skill, AgentSkill, SkillReview, SkillSubmission } from "./types";

export function getSkills(params?: {
  category?: string;
  search?: string;
  sort_by?: string;
  tag?: string;
  limit?: number;
  offset?: number;
}): Promise<SkillBrief[]> {
  const q = new URLSearchParams();
  if (params?.category) q.set("category", params.category);
  if (params?.search) q.set("search", params.search);
  if (params?.sort_by) q.set("sort_by", params.sort_by);
  if (params?.tag) q.set("tag", params.tag);
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  const qs = q.toString();
  return apiGet<SkillBrief[]>(`/skills${qs ? `?${qs}` : ""}`);
}

export function getSkillCategories(): Promise<string[]> {
  return apiGet<string[]>("/skills/categories");
}

export function getSkillTags(): Promise<string[]> {
  return apiGet<string[]>("/skills/tags");
}

export function getTrendingSkills(limit = 10): Promise<SkillBrief[]> {
  return apiGet<SkillBrief[]>(`/skills/trending?limit=${limit}`);
}

export function getSkillBySlug(slug: string): Promise<Skill> {
  return apiGet<Skill>(`/skills/${encodeURIComponent(slug)}`);
}

export function getSkillRecommendations(slug: string, limit = 6): Promise<SkillBrief[]> {
  return apiGet<SkillBrief[]>(`/skills/${encodeURIComponent(slug)}/recommendations?limit=${limit}`);
}

export function getAgentSkills(agentId: string): Promise<AgentSkill[]> {
  return apiGet<AgentSkill[]>(`/skills/agents/${agentId}/installed`);
}

export function installSkill(agentId: string, skillId: string): Promise<AgentSkill> {
  return apiPost<AgentSkill>(`/skills/agents/${agentId}/install`, { skill_id: skillId });
}

export function uninstallSkill(agentId: string, skillId: string): Promise<void> {
  return apiDelete(`/skills/agents/${agentId}/uninstall/${skillId}`);
}

export function toggleAgentSkill(agentId: string, skillId: string, enabled: boolean): Promise<AgentSkill> {
  return apiPatch<AgentSkill>(`/skills/agents/${agentId}/toggle/${skillId}`, { enabled });
}

// --- Reviews ---

export function getSkillReviews(slug: string, limit = 50, offset = 0): Promise<SkillReview[]> {
  return apiGet<SkillReview[]>(`/skills/${encodeURIComponent(slug)}/reviews?limit=${limit}&offset=${offset}`);
}

export function getMyReview(slug: string): Promise<SkillReview | null> {
  return apiGet<SkillReview | null>(`/skills/${encodeURIComponent(slug)}/reviews/mine`);
}

export function createReview(
  slug: string,
  data: { rating: number; title?: string; content?: string },
): Promise<SkillReview> {
  return apiPost<SkillReview>(`/skills/${encodeURIComponent(slug)}/reviews`, data);
}

export function updateReview(
  slug: string,
  data: { rating?: number; title?: string; content?: string },
): Promise<SkillReview> {
  return apiPatch<SkillReview>(`/skills/${encodeURIComponent(slug)}/reviews`, data);
}

export function deleteReview(slug: string): Promise<void> {
  return apiDelete(`/skills/${encodeURIComponent(slug)}/reviews`);
}

// --- Skill Submissions ---

export function submitSkill(data: {
  name: string;
  slug: string;
  summary: string;
  description: string;
  category: string;
  tags?: string[];
  version?: string;
  source_url?: string;
}): Promise<SkillSubmission> {
  return apiPost<SkillSubmission>("/skills/submissions", data);
}

export function getMySubmissions(): Promise<SkillSubmission[]> {
  return apiGet<SkillSubmission[]>("/skills/submissions/mine");
}
