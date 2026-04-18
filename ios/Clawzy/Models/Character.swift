import Foundation

struct CharacterTemplate: Codable, Identifiable {
    let id: String
    let name: String
    let nameReading: String?
    let age: Int?
    let occupation: String?
    let personalityType: String?
    let personalityTraits: [String]?
    let speakingStyle: String?
    let catchphrase: String?
    let interests: [String]?
    let backstory: String?
    let systemPrompt: String
    let greetingMessage: String?
    let sampleDialogues: [SampleDialogue]?
    let avatarColor: String?
    let category: String
    let isPreset: Bool
    let creatorId: String?
    let usageCount: Int
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id, name, age, occupation, backstory, category, interests, catchphrase
        case nameReading = "name_reading"
        case personalityType = "personality_type"
        case personalityTraits = "personality_traits"
        case speakingStyle = "speaking_style"
        case systemPrompt = "system_prompt"
        case greetingMessage = "greeting_message"
        case sampleDialogues = "sample_dialogues"
        case avatarColor = "avatar_color"
        case isPreset = "is_preset"
        case creatorId = "creator_id"
        case usageCount = "usage_count"
        case createdAt = "created_at"
    }
}

struct SampleDialogue: Codable {
    let user: String
    let char: String
}

struct UseCharacterResponse: Codable {
    let agentId: String
    let characterId: String
    let characterName: String

    enum CodingKeys: String, CodingKey {
        case agentId = "agent_id"
        case characterId = "character_id"
        case characterName = "character_name"
    }
}
