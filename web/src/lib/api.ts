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

/** Prevent concurrent refresh requests */
let refreshPromise: Promise<boolean> | null = null;

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
  _isRetry = false,
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

  if (res.status === 401 && !_isRetry) {
    // Don't refresh for login/register endpoints
    const isAuthEndpoint = path.startsWith("/auth/");
    if (!isAuthEndpoint) {
      // Deduplicate concurrent refresh calls
      if (!refreshPromise) {
        refreshPromise = tryRefreshToken().finally(() => { refreshPromise = null; });
      }
      const refreshed = await refreshPromise;
      if (refreshed) {
        return request<T>(path, options, true);
      }
    }
    clearTokens();
    if (typeof window !== "undefined") {
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
  return apiGet<Skill>(`/skills/${slug}`);
}

export function getSkillRecommendations(slug: string, limit = 6): Promise<SkillBrief[]> {
  return apiGet<SkillBrief[]>(`/skills/${slug}/recommendations?limit=${limit}`);
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
  return apiGet<SkillReview[]>(`/skills/${slug}/reviews?limit=${limit}&offset=${offset}`);
}

export function getMyReview(slug: string): Promise<SkillReview | null> {
  return apiGet<SkillReview | null>(`/skills/${slug}/reviews/mine`);
}

export function createReview(
  slug: string,
  data: { rating: number; title?: string; content?: string },
): Promise<SkillReview> {
  return apiPost<SkillReview>(`/skills/${slug}/reviews`, data);
}

export function updateReview(
  slug: string,
  data: { rating?: number; title?: string; content?: string },
): Promise<SkillReview> {
  return apiPatch<SkillReview>(`/skills/${slug}/reviews`, data);
}

export function deleteReview(slug: string): Promise<void> {
  return apiDelete(`/skills/${slug}/reviews`);
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

// --- Memory ---

import type { Memory, WebFetchResult, CodeExecResult, SubtaskResult } from "./types";

export function getMemories(): Promise<Memory[]> {
  return apiGet<Memory[]>("/memory");
}

export function deleteMemory(id: string): Promise<void> {
  return apiDelete(`/memory/${id}`);
}

// --- Tools ---

export function webFetch(url: string): Promise<WebFetchResult> {
  return apiPost<WebFetchResult>("/tools/web-fetch", { url });
}

export function execCode(agentId: string, code: string, language = "python"): Promise<CodeExecResult> {
  return apiPost<CodeExecResult>("/tools/exec", { agent_id: agentId, code, language });
}

// --- Subtasks ---

export function runSubtask(agentId: string, task: string, parentConversationId?: string): Promise<SubtaskResult> {
  return apiPost<SubtaskResult>("/subtasks", { agent_id: agentId, task, parent_conversation_id: parentConversationId });
}
