import Foundation

// MARK: - User

struct User: Codable, Identifiable {
    let id: String
    let email: String
    let name: String
    let credit_balance: Int
    let email_verified: Bool
}

// MARK: - Agent

struct Agent: Codable, Identifiable {
    let id: String
    let name: String
    let model_name: String
    let status: AgentStatus
    let ws_port: Int?
    let created_at: String
}

enum AgentStatus: String, Codable {
    case creating
    case running
    case stopped
    case error
}

// MARK: - Chat

struct ChatMessage: Codable {
    let type: ChatMessageType
    let content: String?
    let message: String?
    let usage: ChatUsage?
    let code: String?
    let status: String?
    let model: String?
    let is_fallback: Bool?
    let conversation_id: String?
}

enum ChatMessageType: String, Codable {
    case message
    case stream
    case done
    case error
    case status
    case agent_status
    case model_switched
    case pong
    case reconnected
}

struct ChatUsage: Codable {
    let credits: Int
    let balance: Int?
}

// MARK: - Conversation

struct Conversation: Codable, Identifiable {
    let id: String
    let agent_id: String
    let title: String?
    let updated_at: String
}

struct Message: Codable, Identifiable {
    let id: String
    let role: MessageRole
    let content: String
    let created_at: String
}

enum MessageRole: String, Codable {
    case user
    case assistant
    case system
}

// MARK: - Models catalog

struct ModelInfo: Codable, Identifiable {
    let id: String
    let name: String
    let provider: String
    let tier: String
    let credits_per_1k_input: Double
    let credits_per_1k_output: Double
    let description: String
}

// MARK: - Billing

struct CreditsInfo: Codable {
    let balance: Int
    let used_this_period: Int
    let plan: String
}

struct PlanInfo: Codable, Identifiable {
    let id: String
    let name: String
    let price_monthly: Double
    let credits_included: Int
    let max_agents: Int
}
