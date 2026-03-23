import SwiftUI

struct ContentView: View {
    @Environment(AuthManager.self) var authManager

    var body: some View {
        Group {
            if authManager.isAuthenticated {
                MainTabView()
            } else {
                WelcomeView()
            }
        }
        .animation(.easeInOut(duration: 0.4), value: authManager.isAuthenticated)
        .task {
            await authManager.tryAutoLogin()
        }
    }
}
