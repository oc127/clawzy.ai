import SwiftUI

struct ContentView: View {
    @Environment(AuthManager.self) var authManager
    @Environment(HealthMonitor.self) var healthMonitor
    @Environment(\.lang) var lang
    @State private var startupDone = false

    var body: some View {
        Group {
            if !startupDone {
                // Startup health check in progress
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.2)
                    Text(lang.t("接続確認中...", en: "Checking connection...", zh: "连接检查中...", ko: "연결 확인 중..."))
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(BrandConfig.backgroundColor)
            } else if !healthMonitor.isBackendOnline {
                BackendOfflineView {
                    Task {
                        await healthMonitor.checkHealth()
                        if healthMonitor.isBackendOnline {
                            await authManager.tryAutoLogin()
                        }
                    }
                }
            } else if authManager.isAuthenticated {
                MainTabView()
            } else {
                WelcomeView()
            }
        }
        .animation(.easeInOut(duration: 0.4), value: authManager.isAuthenticated)
        .animation(.easeInOut(duration: 0.3), value: startupDone)
        .animation(.easeInOut(duration: 0.3), value: healthMonitor.isBackendOnline)
        .task {
            await healthMonitor.checkHealth()
            startupDone = true
            if healthMonitor.isBackendOnline {
                await authManager.tryAutoLogin()
            }
        }
    }
}

// MARK: - Backend offline view

struct BackendOfflineView: View {
    let onRetry: () -> Void
    @Environment(\.lang) var lang

    var body: some View {
        VStack(spacing: 24) {
            Spacer()
            ZStack {
                Circle()
                    .fill(Color.red.opacity(0.10))
                    .frame(width: 88, height: 88)
                Image(systemName: "wifi.slash")
                    .font(.system(size: 40))
                    .foregroundStyle(.red)
            }
            VStack(spacing: 8) {
                Text(lang.t("サーバーに接続できません",
                            en: "Cannot Connect to Server",
                            zh: "无法连接服务器",
                            ko: "서버에 연결할 수 없습니다"))
                    .font(.title3).fontWeight(.semibold)
                Text(lang.t("バックエンドサーバーがオフラインです。しばらく経ってから再試行してください。",
                            en: "The backend server is offline. Please try again later.",
                            zh: "后端服务器已离线，请稍后重试。",
                            ko: "백엔드 서버가 오프라인입니다. 잠시 후 다시 시도해 주세요."))
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
            }
            BrandButton(
                title: lang.t("再試行", en: "Retry", zh: "重试", ko: "재시도"),
                isLoading: false,
                action: onRetry
            )
            .padding(.horizontal, 48)
            Spacer()
        }
        .background(BrandConfig.backgroundColor)
    }
}
