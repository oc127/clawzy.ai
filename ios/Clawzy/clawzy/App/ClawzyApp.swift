import SwiftUI

@main
struct ClawzyApp: App {
    @State private var authManager = AuthManager()
    @State private var languageManager = LanguageManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(authManager)
                .environment(\.lang, languageManager)
        }
    }
}
