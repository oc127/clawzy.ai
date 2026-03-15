export interface Agent {
  id: string;
  name: string;
  model_name: string;
  status: string;
  ws_port: number | null;
  created_at: string;
  last_active_at: string | null;
}

export interface Conversation {
  id: string;
  agent_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  tokens_input: number | null;
  tokens_output: number | null;
  credits_used: number | null;
  model_name: string | null;
  created_at: string;
}

export interface Credits {
  balance: number;
  used_this_period: number;
  plan: string;
}

export interface CreditTransaction {
  id: string;
  amount: number;
  balance_after: number;
  reason: string;
  model_name: string | null;
  tokens_input: number | null;
  tokens_output: number | null;
  created_at: string;
}

export interface Plan {
  id: string;
  name: string;
  price_monthly: number;
  credits_included: number;
  max_agents: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  tier: string;
  credits_per_1k_input: number;
  credits_per_1k_output: number;
  description: string;
}

export interface Skill {
  id: string;
  slug: string;
  name: string;
  summary: string;
  description: string;
  category: string;
  tags: string[] | null;
  icon_url: string | null;
  clawhub_url: string | null;
  author: string | null;
  version: string | null;
  install_count: number;
  is_featured: boolean;
  security_status: string;
  created_at: string;
}

export interface SkillBrief {
  id: string;
  slug: string;
  name: string;
  summary: string;
  category: string;
  tags: string[] | null;
  icon_url: string | null;
  install_count: number;
  is_featured: boolean;
  security_status: string;
}

export interface AgentSkill {
  id: string;
  skill: SkillBrief;
  enabled: boolean;
  installed_at: string;
}
