export interface User {
  id: string
  email: string
  name: string
  credit_balance: number
}

export interface Agent {
  id: string
  name: string
  model_name: string
  status: string
  system_prompt?: string
  created_at: string
  updated_at?: string
}

export interface Conversation {
  id: string
  agent_id: string
  title: string
  created_at: string
  updated_at?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
  conversation_id: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
}

export interface WSMessage {
  type: 'message' | 'switch_model'
  content?: string
  conversation_id?: string
  model?: string
}

export interface WSResponse {
  type: 'stream' | 'done' | 'error'
  content?: string
  usage?: Record<string, number>
  conversation_id?: string
  code?: string
  message?: string
}

export interface MarketTemplate {
  id: string
  name: string
  description: string
  category: string
  model_name: string
  system_prompt: string
  icon?: string
  tags?: string[]
}

export interface MarketPlugin {
  id: string
  name: string
  description: string
  category: string
  version: string
  author: string
  tags?: string[]
}
