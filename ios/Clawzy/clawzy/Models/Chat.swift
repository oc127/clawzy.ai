import Foundation

struct Conversation: Codable, Identifiable {
    let id: String
    let agentId: String
    let title: String
    let createdAt: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case agentId = "agent_id"
        case title
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct Message: Codable, Identifiable {
    let id: String
    let conversationId: String
    let role: MessageRole
    let content: String
    let creditsUsed: Int?
    let modelName: String?
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case conversationId = "conversation_id"
        case role, content
        case creditsUsed = "credits_used"
        case modelName = "model_name"
        case createdAt = "created_at"
    }
}

enum MessageRole: String, Codable {
    case user
    case assistant
    case system
}

// MARK: - WebSocket 消息协议

/// 客户端发送给服务端的消息
struct WSSendMessage: Codable {
    let type: String
    let content: String?
    let model: String?
}

/// 服务端推送给客户端的消息
enum WSReceivedMessage {
    case stream(String)
    case done(usage: WSUsage)
    case error(code: String, message: String)
    case agentStatus(String)
    case unknown
}

struct WSUsage: Codable {
    let credits: Int
    let balance: Int
}

struct WSRawMessage: Codable {
    let type: String
    let content: String?
    let code: String?
    let message: String?
    let status: String?
    let usage: WSUsage?
}
