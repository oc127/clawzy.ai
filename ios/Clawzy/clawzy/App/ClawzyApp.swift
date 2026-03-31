import SwiftUI

@main
struct ClawzyApp: App {
    @State private var authManager = AuthManager()
    @State private var languageManager = LanguageManager()
    @State private var healthMonitor = HealthMonitor()
    @AppStorage("appColorScheme") private var colorScheme: String = "system"

    private var preferredScheme: ColorScheme? {
        switch colorScheme {
        case "light": return .light
        case "dark":  return .dark
        default:      return nil
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(authManager)
                .environment(\.lang, languageManager)
                .environment(healthMonitor)
                .preferredColorScheme(preferredScheme)
                .task { healthMonitor.startMonitoring() }
        }
    }
}
