import SwiftUI

@main
struct ClawzyApp: App {
    @StateObject private var authVM = AuthViewModel()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(authVM)
        }
    }
}

struct RootView: View {
    @EnvironmentObject var authVM: AuthViewModel

    var body: some View {
        Group {
            if authVM.isLoading {
                ProgressView("Loading…")
            } else if authVM.isAuthenticated {
                MainTabView()
            } else {
                LoginView()
            }
        }
        .task {
            await authVM.checkAuth()
        }
    }
}

struct MainTabView: View {
    var body: some View {
        TabView {
            AgentListView()
                .tabItem {
                    Label("Agents", systemImage: "cpu")
                }

            BillingView()
                .tabItem {
                    Label("Billing", systemImage: "creditcard")
                }

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape")
                }
        }
    }
}
