import Foundation
import SwiftUI
import Observation

@Observable
final class AuthManager {
    var currentUser: User?
    var isAuthenticated = false
    var isLoading = false
    var errorMessage: String?

    private let api = APIClient.shared
    private let keychain = KeychainHelper.shared

    // MARK: - 自动登录

    func tryAutoLogin() async {
        guard keychain.readString(for: Constants.accessTokenKey) != nil else { return }
        isLoading = true
        defer { Task { await MainActor.run { self.isLoading = false } } }
        do {
            let user: User = try await api.request(Constants.API.me)
            await MainActor.run {
                self.currentUser = user
                self.isAuthenticated = true
                self.errorMessage = nil
            }
        } catch APIError.unauthorized {
            // Access token expired — try refresh token before giving up
            await tryRefreshToken()
        } catch {
            // Other error (network etc) — log out silently
            await MainActor.run { self.logout() }
        }
    }

    private func tryRefreshToken() async {
        guard let refreshToken = keychain.readString(for: Constants.refreshTokenKey) else {
            await MainActor.run { self.logout() }
            return
        }
        do {
            let body = RefreshRequest(refreshToken: refreshToken)
            let response: AuthResponse = try await api.request(Constants.API.refresh, method: "POST", body: body)
            saveTokens(response)
            let user: User = try await api.request(Constants.API.me)
            await MainActor.run {
                self.currentUser = user
                self.isAuthenticated = true
                self.errorMessage = nil
            }
        } catch {
            // Refresh token also expired — log out
            await MainActor.run { self.logout() }
        }
    }

    // MARK: - 登录

    func login(email: String, password: String) async {
        await MainActor.run {
            isLoading = true
            errorMessage = nil
        }
        defer { Task { await MainActor.run { self.isLoading = false } } }
        do {
            let body = LoginRequest(email: email.lowercased().trimmingCharacters(in: .whitespaces), password: password)
            let response: AuthResponse = try await api.request(Constants.API.login, method: "POST", body: body)
            saveTokens(response)
            let user: User = try await api.request(Constants.API.me)
            await MainActor.run {
                self.currentUser = user
                self.isAuthenticated = true
            }
        } catch {
            await MainActor.run { self.errorMessage = "[\(type(of: error))] \(error.localizedDescription)" }
        }
    }

    // MARK: - 注册

    func register(name: String, email: String, password: String) async {
        await MainActor.run {
            isLoading = true
            errorMessage = nil
        }
        defer { Task { await MainActor.run { self.isLoading = false } } }
        do {
            let body = RegisterRequest(email: email.lowercased().trimmingCharacters(in: .whitespaces), password: password, name: name)
            let response: AuthResponse = try await api.request(Constants.API.register, method: "POST", body: body)
            saveTokens(response)
            let user: User = try await api.request(Constants.API.me)
            await MainActor.run {
                self.currentUser = user
                self.isAuthenticated = true
            }
        } catch {
            await MainActor.run { self.errorMessage = error.localizedDescription }
        }
    }

    // MARK: - 登出

    func logout() {
        keychain.delete(for: Constants.accessTokenKey)
        keychain.delete(for: Constants.refreshTokenKey)
        currentUser = nil
        isAuthenticated = false
        errorMessage = nil
    }

    private func saveTokens(_ response: AuthResponse) {
        keychain.saveString(response.accessToken, for: Constants.accessTokenKey)
        keychain.saveString(response.refreshToken, for: Constants.refreshTokenKey)
    }
}
