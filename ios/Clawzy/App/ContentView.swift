import SwiftUI

struct ContentView: View {
    @Environment(AuthManager.self) var authManager

    var body: some View {
        Group {
            if authManager.isAuthenticated {
                MainTabView()
            } else {
                LoginView()
            }
        }
        .animation(.easeInOut, value: authManager.isAuthenticated)
        .task {
            // 尝试用 Keychain 中保存的 token 自动登录
            await authManager.tryAutoLogin()
        }
    }
}
