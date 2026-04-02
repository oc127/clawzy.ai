import type { Agent, Conversation, Message, TokenResponse, User, MarketTemplate } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://nipponclaw.com/api/v1'

function getTokens() {
  if (typeof window === 'undefined') return { access: null, refresh: null }
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  }
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

export function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

async function refreshAccessToken(): Promise<string | null> {
  const { refresh } = getTokens()
  if (!refresh) return null

  try {
    const res = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    })
    if (!res.ok) {
      clearTokens()
      return null
    }
    const data: TokenResponse = await res.json()
    setTokens(data.access_token, data.refresh_token)
    return data.access_token
  } catch {
    clearTokens()
    return null
  }
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const { access } = getTokens()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }
  if (access) {
    headers['Authorization'] = `Bearer ${access}`
  }

  let res = await fetch(`${API_URL}${path}`, { ...options, headers })

  // Auto-refresh on 401
  if (res.status === 401 && access) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`
      res = await fetch(`${API_URL}${path}`, { ...options, headers })
    } else {
      clearTokens()
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
      throw new Error('Session expired')
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }

  return res.json()
}

// Auth
export async function login(email: string, password: string): Promise<TokenResponse> {
  const data = await apiFetch<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  setTokens(data.access_token, data.refresh_token)
  return data
}

export async function register(email: string, password: string, name: string): Promise<TokenResponse> {
  const data = await apiFetch<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, name }),
  })
  setTokens(data.access_token, data.refresh_token)
  return data
}

// Users
export async function getMe(): Promise<User> {
  return apiFetch<User>('/users/me')
}

// Agents
export async function listAgents(): Promise<Agent[]> {
  return apiFetch<Agent[]>('/agents')
}

export async function getAgent(agentId: string): Promise<Agent> {
  return apiFetch<Agent>(`/agents/${agentId}`)
}

export async function createAgent(name: string, modelName: string, systemPrompt?: string): Promise<Agent> {
  return apiFetch<Agent>('/agents', {
    method: 'POST',
    body: JSON.stringify({ name, model_name: modelName, system_prompt: systemPrompt }),
  })
}

export async function deleteAgent(agentId: string): Promise<void> {
  await apiFetch(`/agents/${agentId}`, { method: 'DELETE' })
}

// Conversations
export async function listConversations(agentId: string): Promise<Conversation[]> {
  return apiFetch<Conversation[]>(`/chat/agents/${agentId}/conversations`)
}

export async function getConversationMessages(conversationId: string): Promise<Message[]> {
  return apiFetch<Message[]>(`/chat/conversations/${conversationId}/messages`)
}

// Market
export async function listTemplates(): Promise<MarketTemplate[]> {
  return apiFetch<MarketTemplate[]>('/templates')
}

// WebSocket helper
export function createChatWebSocket(agentId: string): WebSocket | null {
  const { access } = getTokens()
  if (!access) return null

  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'wss://nipponclaw.com/api/v1'
  return new WebSocket(`${wsUrl}/ws/chat/${agentId}?token=${access}`)
}
