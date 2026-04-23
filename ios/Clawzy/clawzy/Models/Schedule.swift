import Foundation

struct AgentTask: Codable, Identifiable {
    let id: String
    let agentId: String?
    let userId: String
    let title: String
    let description: String?
    let dueDate: Date?
    let priority: String
    let status: String
    let category: String?
    let createdBy: String
    let completedAt: Date?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id, title, description, priority, status, category
        case agentId = "agent_id"
        case userId = "user_id"
        case dueDate = "due_date"
        case createdBy = "created_by"
        case completedAt = "completed_at"
        case createdAt = "created_at"
    }
}

struct AgentTaskCreate: Codable {
    let title: String
    let description: String?
    let dueDate: Date?
    let priority: String
    let category: String?

    enum CodingKeys: String, CodingKey {
        case title, description, priority, category
        case dueDate = "due_date"
    }
}
