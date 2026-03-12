const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

interface ApiOptions {
  method?: string;
  body?: unknown;
  token?: string;
}

export async function apiFetch<T>(path: string, opts: ApiOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (opts.token) {
    headers['Authorization'] = `Bearer ${opts.token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method: opts.method || 'GET',
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error ${res.status}`);
  }

  return res.json();
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export async function login(email: string, password: string): Promise<AuthTokens> {
  return apiFetch<AuthTokens>('/auth/login', {
    method: 'POST',
    body: { email, password },
  });
}

export async function register(email: string, password: string, name: string): Promise<AuthTokens> {
  return apiFetch<AuthTokens>('/auth/register', {
    method: 'POST',
    body: { email, password, name },
  });
}

export interface Agent {
  id: string;
  name: string;
  model_name: string;
  status: string;
  created_at: string;
}

export async function getAgents(token: string): Promise<Agent[]> {
  return apiFetch<Agent[]>('/agents', { token });
}

export async function createAgent(token: string, name: string, model_name: string): Promise<Agent> {
  return apiFetch<Agent>('/agents', {
    method: 'POST',
    body: { name, model_name },
    token,
  });
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  credit_balance: number;
  created_at: string;
}

export async function getProfile(token: string): Promise<UserProfile> {
  return apiFetch<UserProfile>('/users/me', { token });
}

export interface Conversation {
  id: string;
  agent_id: string;
  title: string;
  created_at: string;
}

export async function getConversations(token: string, agentId: string): Promise<Conversation[]> {
  return apiFetch<Conversation[]>(`/agents/${agentId}/conversations`, { token });
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

export async function getMessages(token: string, conversationId: string): Promise<Message[]> {
  return apiFetch<Message[]>(`/conversations/${conversationId}/messages`, { token });
}
