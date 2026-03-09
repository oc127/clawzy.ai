import Foundation
import KeychainAccess

/// Manages JWT tokens in Keychain and handles login/register/refresh flows.
@MainActor
final class AuthService {
    static let shared = AuthService()

    private let keychain = Keychain(service: "ai.clawzy.app")
    private let accessTokenKey = "access_token"
    private let refreshTokenKey = "refresh_token"

    private(set) var isRefreshing = false

    // MARK: - Token access

    var accessToken: String? {
        keychain[accessTokenKey]
    }

    var refreshToken: String? {
        keychain[refreshTokenKey]
    }

    var isLoggedIn: Bool {
        accessToken != nil
    }

    // MARK: - Store / clear

    func storeTokens(access: String, refresh: String) {
        keychain[accessTokenKey] = access
        keychain[refreshTokenKey] = refresh
    }

    func clearTokens() {
        keychain[accessTokenKey] = nil
        keychain[refreshTokenKey] = nil
    }

    // MARK: - Auth API calls

    func login(email: String, password: String) async throws {
        let body: [String: String] = ["email": email, "password": password]
        let tokens: TokenResponse = try await APIClient.shared.request(
            path: "/auth/login",
            method: "POST",
            body: body,
            authenticated: false
        )
        storeTokens(access: tokens.access_token, refresh: tokens.refresh_token)
    }

    func register(email: String, password: String, name: String) async throws {
        let body: [String: String] = ["email": email, "password": password, "name": name]
        let tokens: TokenResponse = try await APIClient.shared.request(
            path: "/auth/register",
            method: "POST",
            body: body,
            authenticated: false
        )
        storeTokens(access: tokens.access_token, refresh: tokens.refresh_token)
    }

    func logout() {
        clearTokens()
    }

    /// Attempts to refresh the access token. Returns `true` on success.
    func tryRefresh() async -> Bool {
        guard let rt = refreshToken else { return false }
        isRefreshing = true
        defer { isRefreshing = false }

        do {
            var request = URLRequest(url: URL(string: "\(Configuration.apiBaseURL)/auth/refresh")!)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONEncoder().encode(["refresh_token": rt])

            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
                return false
            }
            let tokens = try JSONDecoder().decode(TokenResponse.self, from: data)
            storeTokens(access: tokens.access_token, refresh: tokens.refresh_token)
            return true
        } catch {
            return false
        }
    }

    func forgotPassword(email: String) async throws {
        let _: MessageResponse = try await APIClient.shared.request(
            path: "/auth/forgot-password",
            method: "POST",
            body: ["email": email],
            authenticated: false
        )
    }
}

struct TokenResponse: Codable {
    let access_token: String
    let refresh_token: String
}

struct MessageResponse: Codable {
    let message: String
}
