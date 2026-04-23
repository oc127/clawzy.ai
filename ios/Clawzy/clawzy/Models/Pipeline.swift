import Foundation

struct TaskPipeline: Codable, Identifiable {
    let id: String
    let userId: String
    let title: String
    let description: String?
    let status: PipelineStatus
    let originalPrompt: String?
    let plan: [String: AnyCodable]?
    let resultSummary: String?
    let totalSteps: Int
    let completedSteps: Int
    let createdAt: String
    let completedAt: String?
    var steps: [PipelineStep]?

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case title
        case description
        case status
        case originalPrompt = "original_prompt"
        case plan
        case resultSummary = "result_summary"
        case totalSteps = "total_steps"
        case completedSteps = "completed_steps"
        case createdAt = "created_at"
        case completedAt = "completed_at"
        case steps
    }
}

enum PipelineStatus: String, Codable {
    case planning
    case ready
    case running
    case evaluating
    case completed
    case failed

    var label: String {
        switch self {
        case .planning:   return "計画中"
        case .ready:      return "準備完了"
        case .running:    return "実行中"
        case .evaluating: return "評価中"
        case .completed:  return "完了"
        case .failed:     return "失敗"
        }
    }

    var labelEn: String {
        switch self {
        case .planning:   return "Planning"
        case .ready:      return "Ready"
        case .running:    return "Running"
        case .evaluating: return "Evaluating"
        case .completed:  return "Completed"
        case .failed:     return "Failed"
        }
    }
}

struct PipelineStep: Codable, Identifiable {
    let id: String
    let pipelineId: String
    let agentId: String?
    let stepOrder: Int
    let title: String
    let description: String?
    let status: StepStatus
    let agentRole: String
    let outputData: [String: String]?
    let evaluationScore: Double?
    let evaluationNotes: String?
    let dependsOn: [Int]?
    let startedAt: String?
    let completedAt: String?
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case pipelineId = "pipeline_id"
        case agentId = "agent_id"
        case stepOrder = "step_order"
        case title
        case description
        case status
        case agentRole = "agent_role"
        case outputData = "output_data"
        case evaluationScore = "evaluation_score"
        case evaluationNotes = "evaluation_notes"
        case dependsOn = "depends_on"
        case startedAt = "started_at"
        case completedAt = "completed_at"
        case createdAt = "created_at"
    }
}

enum StepStatus: String, Codable {
    case pending
    case running
    case completed
    case failed
    case skipped
}

struct CreatePipelineRequest: Codable {
    let prompt: String
}

struct PipelineListResponse: Codable {
    let pipelines: [TaskPipeline]
    let total: Int
}

// Minimal wrapper for arbitrary JSON values in the plan field
struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) { self.value = value }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let v = try? container.decode(Bool.self)   { value = v; return }
        if let v = try? container.decode(Int.self)    { value = v; return }
        if let v = try? container.decode(Double.self) { value = v; return }
        if let v = try? container.decode(String.self) { value = v; return }
        if let v = try? container.decode([String: AnyCodable].self) { value = v; return }
        if let v = try? container.decode([AnyCodable].self) { value = v; return }
        value = NSNull()
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case let v as Bool:                    try container.encode(v)
        case let v as Int:                     try container.encode(v)
        case let v as Double:                  try container.encode(v)
        case let v as String:                  try container.encode(v)
        case let v as [String: AnyCodable]:    try container.encode(v)
        case let v as [AnyCodable]:            try container.encode(v)
        default:                               try container.encodeNil()
        }
    }
}
