import Foundation

struct CreditsInfo: Codable {
    let balance: Int
    let usedThisPeriod: Int
    let plan: String

    enum CodingKeys: String, CodingKey {
        case balance
        case usedThisPeriod = "used_this_period"
        case plan
    }
}

struct CreditTransaction: Codable, Identifiable {
    let id: String
    let amount: Int
    let balanceAfter: Int
    let reason: String
    let modelName: String?
    let tokensInput: Int?
    let tokensOutput: Int?
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id, amount
        case balanceAfter = "balance_after"
        case reason
        case modelName = "model_name"
        case tokensInput = "tokens_input"
        case tokensOutput = "tokens_output"
        case createdAt = "created_at"
    }
}

struct AIModel: Codable, Identifiable {
    let id: String
    let name: String
    let provider: String
    let tier: String
    let creditsPerInputK: Double
    let creditsPerOutputK: Double
    let description: String

    enum CodingKeys: String, CodingKey {
        case id, name, provider, tier, description
        case creditsPerInputK = "credits_per_1k_input"
        case creditsPerOutputK = "credits_per_1k_output"
    }
}
