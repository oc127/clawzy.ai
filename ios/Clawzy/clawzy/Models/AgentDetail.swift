import Foundation

// MARK: - Agent Tool

struct AgentTool: Codable, Identifiable {
    let name: String
    let description: String
    var enabled: Bool

    var id: String { name }

    enum CodingKeys: String, CodingKey {
        case name, description, enabled
    }
}

// MARK: - Agent Memory

struct AgentMemory: Codable, Identifiable {
    let id: String
    let content: String
    let type: String
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id, content, type
        case createdAt = "created_at"
    }
}

// MARK: - Agent Skill

struct AgentSkill: Codable, Identifiable {
    let name: String
    let description: String
    let version: String?

    var id: String { name }
}

// MARK: - Scheduled Task

struct AgentTask: Codable, Identifiable {
    let id: String
    let cronExpression: String
    let prompt: String
    let description: String
    var enabled: Bool
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case cronExpression = "cron_expression"
        case prompt, description, enabled
        case createdAt = "created_at"
    }
}

struct CreateTaskRequest: Codable {
    let cronExpression: String
    let prompt: String
    let description: String

    enum CodingKeys: String, CodingKey {
        case cronExpression = "cron_expression"
        case prompt, description
    }
}

struct UpdateTaskRequest: Codable {
    let enabled: Bool?
    let cronExpression: String?
    let prompt: String?
    let description: String?

    enum CodingKeys: String, CodingKey {
        case enabled
        case cronExpression = "cron_expression"
        case prompt, description
    }
}

// MARK: - Agent Channel

struct AgentChannel: Codable, Identifiable {
    let id: String
    let type: String           // "telegram" or "line"
    let config: [String: String]?
    let status: String?
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id, type, config, status
        case createdAt = "created_at"
    }
}

struct CreateChannelRequest: Codable {
    let type: String
    let config: [String: String]
}
