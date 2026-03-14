import { getAccessToken, clearTokens } from "./auth";

const API_BASE = "/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
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

import type { SkillBrief, Skill, AgentSkill } from "./types";

export function getSkills(params?: {
  category?: string;
  search?: string;
  sort_by?: string;
  limit?: number;
  offset?: number;
}): Promise<SkillBrief[]> {
  const q = new URLSearchParams();
  if (params?.category) q.set("category", params.category);
  if (params?.search) q.set("search", params.search);
  if (params?.sort_by) q.set("sort_by", params.sort_by);
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  const qs = q.toString();
  return apiGet<SkillBrief[]>(`/skills${qs ? `?${qs}` : ""}`);
}

export function getSkillCategories(): Promise<string[]> {
  return apiGet<string[]>("/skills/categories");
}

export function getTrendingSkills(limit = 10): Promise<SkillBrief[]> {
  return apiGet<SkillBrief[]>(`/skills/trending?limit=${limit}`);
}

export function getSkillBySlug(slug: string): Promise<Skill> {
  return apiGet<Skill>(`/skills/${slug}`);
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
