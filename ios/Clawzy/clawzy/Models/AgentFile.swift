import Foundation

struct AgentFile: Codable, Identifiable {
    let id: String
    let agentId: String?
    let userId: String
    let filename: String
    let fileType: String?
    let fileSize: Int?
    let storagePath: String?
    let description: String?
    let createdBy: String
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id, filename, description
        case agentId = "agent_id"
        case userId = "user_id"
        case fileType = "file_type"
        case fileSize = "file_size"
        case storagePath = "storage_path"
        case createdBy = "created_by"
        case createdAt = "created_at"
    }
}
