import Foundation

enum Constants {
    // ⚠️ 修改为你的后端地址
    // 本地开发时用 http://localhost:8000
    // 部署后改为 https://clawzy.ai
    static let baseURL = "https://clawzy.ai"
    static let wsBaseURL = "wss://clawzy.ai"

    // Keychain keys
    static let accessTokenKey = "clawzy_access_token"
    static let refreshTokenKey = "clawzy_refresh_token"

    // API paths
    enum API {
        static let register = "/api/v1/auth/register"
        static let login = "/api/v1/auth/login"
        static let refresh = "/api/v1/auth/refresh"
        static let me = "/api/v1/users/me"
        static let agents = "/api/v1/agents"
        static let models = "/api/v1/models"
        static let templates = "/api/v1/templates"
        static let credits = "/api/v1/billing/credits"
        static let creditsTransactions = "/api/v1/billing/credits/transactions"

        static let backupExport = "/api/v1/backup/export"

        static let clawHubSearch = "/api/v1/clawhub/search"
        static let clawHubPopular = "/api/v1/clawhub/popular"
        static let clawHubInstall = "/api/v1/clawhub/install"

        static func agent(_ id: String) -> String { "/api/v1/agents/\(id)" }
        static func agentStart(_ id: String) -> String { "/api/v1/agents/\(id)/start" }
        static func agentStop(_ id: String) -> String { "/api/v1/agents/\(id)/stop" }
        static func agentPlugins(_ id: String) -> String { "/api/v1/agents/\(id)/plugins" }
        static func agentPlugin(_ id: String, slug: String) -> String { "/api/v1/agents/\(id)/plugins/\(slug)" }
        static func wsChat(_ agentId: String) -> String { "/api/v1/ws/chat/\(agentId)" }
        static func conversations(_ agentId: String) -> String { "/api/v1/agents/\(agentId)/conversations" }
        static func messages(_ conversationId: String) -> String { "/api/v1/conversations/\(conversationId)/messages" }
        static func clawHubSkill(_ slug: String) -> String { "/api/v1/clawhub/skills/\(slug)" }
    }
}
