import Foundation

@MainActor
final class AuthViewModel: ObservableObject {
    @Published var isAuthenticated = false
    @Published var isLoading = true
    @Published var currentUser: User?
    @Published var errorMessage: String?

    private let auth = AuthService.shared

    func checkAuth() async {
        isLoading = true
        defer { isLoading = false }

        guard auth.isLoggedIn else {
            isAuthenticated = false
            return
        }

        // Validate token by fetching user profile
        do {
            let user: User = try await APIClient.shared.request(path: "/users/me")
            currentUser = user
            isAuthenticated = true
        } catch {
            // Token expired and refresh failed
            isAuthenticated = false
        }
    }

    func login(email: String, password: String) async {
        errorMessage = nil
        do {
            try await auth.login(email: email, password: password)
            let user: User = try await APIClient.shared.request(path: "/users/me")
            currentUser = user
            isAuthenticated = true
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func register(email: String, password: String, name: String) async {
        errorMessage = nil
        do {
            try await auth.register(email: email, password: password, name: name)
            let user: User = try await APIClient.shared.request(path: "/users/me")
            currentUser = user
            isAuthenticated = true
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func logout() {
        auth.logout()
        isAuthenticated = false
        currentUser = nil
    }
}
