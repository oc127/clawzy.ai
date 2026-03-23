import Foundation

struct Agent: Codable, Identifiable {
    let id: String
    let userId: String?
    let name: String
    let modelName: String
    let containerId: String?
    let status: AgentStatus
    let wsPort: Int?
    let createdAt: String
    let lastActiveAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case name
        case modelName = "model_name"
        case containerId = "container_id"
        case status
        case wsPort = "ws_port"
        case createdAt = "created_at"
        case lastActiveAt = "last_active_at"
    }
}

enum AgentStatus: String, Codable {
    case creating
    case running
    case stopped
    case error
}

struct CreateAgentRequest: Codable {
    let name: String
    let modelName: String

    enum CodingKeys: String, CodingKey {
        case name
        case modelName = "model_name"
    }
}
