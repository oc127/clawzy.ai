import SwiftUI

// MARK: - App Language

enum AppLanguage: String, CaseIterable, Identifiable {
    case japanese = "ja"
    case english  = "en"
    case chinese  = "zh"
    case korean   = "ko"

    var id: String { rawValue }

    var badge: String {
        switch self {
        case .japanese: return "JP"
        case .english:  return "EN"
        case .chinese:  return "ZH"
        case .korean:   return "KR"
        }
    }

    var localName: String {
        switch self {
        case .japanese: return "日本語"
        case .english:  return "English"
        case .chinese:  return "中文"
        case .korean:   return "한국어"
        }
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @Environment(AuthManager.self) var authManager
    @Environment(AgentService.self) var agentService
    @Environment(\.lang) var lang
    @AppStorage("appColorScheme") private var colorScheme: String = "system"
    @State private var isExporting = false
    @State private var exportData: Data?
    @State private var exportError: String?
    @State private var showExportShare = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 12) {
                    // Profile card
                    if let user = authManager.currentUser {
                        profileCard(user: user)
                        creditsCard(user: user)
                    }

                    // Agent management
                    if !agentService.agents.isEmpty {
                        agentManagementCard
                    }

                    // Appearance
                    appearanceCard

                    // Language
                    languageCard

                    // Data
                    dataCard

                    // About
                    aboutCard

                    // Logout
                    logoutCard
                }
                .padding(.horizontal, 16)
                .padding(.top, 12)
                .padding(.bottom, 24)
            }
            .background(BrandConfig.darkBg)
            .navigationTitle(lang.t("設定", en: "Settings", zh: "设置", ko: "설정"))
            .navigationBarTitleDisplayMode(.inline)
            .alert(lang.t("エラー", en: "Error", zh: "错误", ko: "오류"),
                   isPresented: Binding(get: { exportError != nil },
                                        set: { if !$0 { exportError = nil } })) {
                Button(lang.t("OK", en: "OK", zh: "确定", ko: "확인")) { exportError = nil }
            } message: {
                Text(exportError ?? "")
            }
        }
    }

    // MARK: - Section cards

    private func profileCard(user: User) -> some View {
        SettingsCard {
            HStack(spacing: 16) {
                ZStack {
                    Circle()
                        .fill(BrandConfig.brand.opacity(0.12))
                        .frame(width: 60, height: 60)
                    Text(String(user.name.prefix(1)).uppercased())
                        .font(.title2).fontWeight(.bold)
                        .foregroundStyle(BrandConfig.brand)
                }
                VStack(alignment: .leading, spacing: 4) {
                    Text(user.name)
                        .font(.headline).fontWeight(.semibold)
                    Text(user.email)
                        .font(.subheadline).foregroundStyle(.secondary)
                }
                Spacer()
            }
            .padding(16)
        }
    }

    private func creditsCard(user: User) -> some View {
        SettingsCard {
            VStack(spacing: 0) {
                SettingsSectionHeader(
                    title: lang.t("クレジット", en: "Credits", zh: "点数", ko: "크레딧"),
                    icon: "bolt.fill",
                    color: BrandConfig.brand
                )
                Divider().padding(.horizontal, 16)
                HStack {
                    Text(lang.t("残高", en: "Balance", zh: "余额", ko: "잔액"))
                        .foregroundStyle(.primary)
                    Spacer()
                    Text("\(user.creditBalance)")
                        .font(.title3).fontWeight(.bold)
                        .foregroundStyle(BrandConfig.brand)
                    Text("pts")
                        .font(.caption).fontWeight(.medium)
                        .foregroundStyle(.secondary)
                }
                .padding(16)
            }
        }
    }

    private var agentManagementCard: some View {
        SettingsCard {
            VStack(spacing: 0) {
                SettingsSectionHeader(
                    title: lang.t("エージェント管理", en: "Agent Management", zh: "助手管理", ko: "에이전트 관리"),
                    icon: "person.crop.circle.fill",
                    color: Color(UIColor.secondaryLabel)
                )
                ForEach(Array(agentService.agents.enumerated()), id: \.element.id) { index, agent in
                    if index > 0 { Divider().padding(.horizontal, 16) }
                    NavigationLink {
                        InstalledPluginsView(agent: agent)
                    } label: {
                        HStack(spacing: 12) {
                            Text("🤖").font(.title3)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(agent.name)
                                    .font(.subheadline).fontWeight(.medium)
                                    .foregroundStyle(.primary)
                                Text(lang.t("インストール済みプラグイン", en: "Installed Plugins", zh: "已安装插件", ko: "설치된 플러그인"))
                                    .font(.caption).foregroundStyle(.secondary)
                            }
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.caption).fontWeight(.semibold)
                                .foregroundStyle(.secondary)
                        }
                        .padding(16)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private var appearanceCard: some View {
        SettingsCard {
            VStack(spacing: 0) {
                SettingsSectionHeader(
                    title: lang.t("外観", en: "Appearance", zh: "外观", ko: "외관"),
                    icon: "paintbrush.fill",
                    color: Color(UIColor.secondaryLabel)
                )
                Divider().padding(.horizontal, 16)
                HStack {
                    Text(lang.t("テーマ", en: "Theme", zh: "主题", ko: "테마"))
                        .foregroundStyle(.primary)
                    Spacer()
                    Picker("", selection: $colorScheme) {
                        Text(lang.t("自動", en: "Auto", zh: "自动", ko: "자동")).tag("system")
                        Image(systemName: "sun.max.fill").tag("light")
                        Image(systemName: "moon.fill").tag("dark")
                    }
                    .pickerStyle(.segmented)
                    .frame(width: 130)
                }
                .padding(16)
            }
        }
    }

    private var languageCard: some View {
        SettingsCard {
            VStack(spacing: 0) {
                SettingsSectionHeader(
                    title: lang.t("言語", en: "Language", zh: "语言", ko: "언어"),
                    icon: "globe",
                    color: Color(UIColor.secondaryLabel)
                )
                Divider().padding(.horizontal, 16)
                NavigationLink {
                    languagePickerView
                } label: {
                    HStack {
                        Text(AppLanguage(rawValue: lang.current)?.localName ?? "日本語")
                            .foregroundStyle(.primary)
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.caption).fontWeight(.semibold)
                            .foregroundStyle(.secondary)
                    }
                    .padding(16)
                }
                .buttonStyle(.plain)
            }
        }
    }

    private var languagePickerView: some View {
        List {
            ForEach(AppLanguage.allCases) { language in
                Button {
                    lang.current = language.rawValue
                } label: {
                    HStack(spacing: 12) {
                        Text(language.badge)
                            .font(.caption.bold())
                            .foregroundStyle(BrandConfig.brand)
                            .frame(width: 32, height: 22)
                            .background(BrandConfig.brand.opacity(0.10))
                            .clipShape(RoundedRectangle(cornerRadius: 6))
                        Text(language.localName)
                            .foregroundStyle(.primary)
                        Spacer()
                        if lang.current == language.rawValue {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(BrandConfig.brand)
                        }
                    }
                }
            }
        }
        .navigationTitle(lang.t("言語", en: "Language", zh: "语言", ko: "언어"))
    }

    private var dataCard: some View {
        SettingsCard {
            VStack(spacing: 0) {
                SettingsSectionHeader(
                    title: lang.t("データ", en: "Data", zh: "数据", ko: "데이터"),
                    icon: "externaldrive.fill",
                    color: Color(UIColor.secondaryLabel)
                )
                Divider().padding(.horizontal, 16)
                Button {
                    Task { await exportUserData() }
                } label: {
                    HStack {
                        if isExporting {
                            ProgressView().padding(.trailing, 4)
                            Text(lang.t("エクスポート中...", en: "Exporting...", zh: "导出中...", ko: "내보내는 중..."))
                                .foregroundStyle(.secondary)
                        } else {
                            Text(lang.t("データをエクスポート", en: "Export Data", zh: "导出数据", ko: "데이터 내보내기"))
                                .foregroundStyle(BrandConfig.brand)
                        }
                        Spacer()
                        Image(systemName: "square.and.arrow.up")
                            .foregroundStyle(BrandConfig.brand)
                    }
                    .padding(16)
                }
                .buttonStyle(.plain)
                .disabled(isExporting)
                .sheet(isPresented: $showExportShare) {
                    if let data = exportData {
                        ShareSheet(items: [data as Any])
                    }
                }
            }
        }
    }

    private var aboutCard: some View {
        SettingsCard {
            VStack(spacing: 0) {
                SettingsSectionHeader(
                    title: lang.t("このアプリについて", en: "About", zh: "关于", ko: "앱 정보"),
                    icon: "info.circle.fill",
                    color: Color(UIColor.secondaryLabel)
                )
                Divider().padding(.horizontal, 16)
                HStack {
                    Text(lang.t("バージョン", en: "Version", zh: "版本", ko: "버전"))
                    Spacer()
                    Text("1.0.0").foregroundStyle(.secondary)
                }
                .padding(16)

                Divider().padding(.horizontal, 16)

                Link(destination: URL(string: BrandConfig.privacyURL)!) {
                    HStack {
                        Text(lang.t("\(BrandConfig.appName) を開く", en: "Open \(BrandConfig.appName)", zh: "打开 \(BrandConfig.appName)", ko: "\(BrandConfig.appName) 열기"))
                            .foregroundStyle(BrandConfig.brand)
                        Spacer()
                        Image(systemName: "safari")
                            .foregroundStyle(BrandConfig.brand)
                    }
                    .padding(16)
                }

                Divider().padding(.horizontal, 16)

                Link(destination: URL(string: BrandConfig.termsURL)!) {
                    HStack {
                        Text(lang.t("利用規約", en: "Terms", zh: "使用条款", ko: "이용약관"))
                            .foregroundStyle(BrandConfig.brand)
                        Spacer()
                        Image(systemName: "doc.text")
                            .foregroundStyle(BrandConfig.brand)
                    }
                    .padding(16)
                }
            }
        }
    }

    private var logoutCard: some View {
        SettingsCard {
            Button(role: .destructive) {
                authManager.logout()
            } label: {
                HStack {
                    Spacer()
                    Image(systemName: "rectangle.portrait.and.arrow.right")
                    Text(lang.t("ログアウト", en: "Logout", zh: "退出登录", ko: "로그아웃"))
                        .fontWeight(.semibold)
                    Spacer()
                }
                .padding(16)
                .foregroundStyle(.red)
            }
        }
    }

    // MARK: - Export

    private func exportUserData() async {
        await MainActor.run { isExporting = true }
        defer { Task { @MainActor in isExporting = false } }

        guard let url = URL(string: Constants.baseURL + Constants.API.backupExport) else { return }
        var req = URLRequest(url: url)
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = KeychainHelper.shared.readString(for: Constants.accessTokenKey) {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        do {
            let (data, _) = try await URLSession.shared.data(for: req)
            await MainActor.run {
                exportData = data
                showExportShare = true
            }
        } catch {
            await MainActor.run { exportError = error.localizedDescription }
        }
    }
}

// MARK: - Reusable card container

private struct SettingsCard<Content: View>: View {
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(spacing: 0) {
            content()
        }
        .background(BrandConfig.darkSurface)
        .clipShape(RoundedRectangle(cornerRadius: BrandConfig.Radius.card))
    }
}

// MARK: - Section header

private struct SettingsSectionHeader: View {
    let title: String
    let icon: String
    let color: Color

    var body: some View {
        HStack(spacing: 10) {
            ZStack {
                RoundedRectangle(cornerRadius: BrandConfig.Spacing.sm)
                    .fill(color.opacity(0.12))
                    .frame(width: 32, height: 32)
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundStyle(color)
            }
            Text(title)
                .font(.subheadline).fontWeight(.semibold)
                .foregroundStyle(.primary)
            Spacer()
        }
        .padding(16)
    }
}

// MARK: - Share sheet

struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}
