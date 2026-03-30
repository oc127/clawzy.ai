import Foundation

struct User: Codable, Identifiable {
    let id: String
    let email: String
    let name: String
    let avatarUrl: String?
    let creditBalance: Int
    let stripeCustomerId: String?
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id, email, name
        case avatarUrl = "avatar_url"
        case creditBalance = "credit_balance"
        case stripeCustomerId = "stripe_customer_id"
        case createdAt = "created_at"
    }
}

struct AuthResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case tokenType = "token_type"
    }
}

struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct RegisterRequest: Codable {
    let email: String
    let password: String
    let name: String
}

struct RefreshRequest: Codable {
    let refreshToken: String

    enum CodingKeys: String, CodingKey {
        case refreshToken = "refresh_token"
    }
}
