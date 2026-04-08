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
    @AppStorage("securityEnvProtection")  private var envProtection: Bool  = true
    @AppStorage("securityDataProtection") private var dataProtection: Bool = true
    @AppStorage("securitySkillScan")      private var skillScan: Bool      = true
    @State private var isExporting = false
    @State private var exportData: Data?
    @State private var exportError: String?
    @State private var showExportShare = false
    @State private var showDeleteConfirm = false
    @State private var isDeletingData = false
    @State private var deleteError: String?

    var body: some View {
        NavigationStack {
            List {
                // MARK: アカウント
                if let user = authManager.currentUser {
                    Section(lang.t("アカウント", en: "Account", zh: "账户", ko: "계정")) {
                        HStack(spacing: 14) {
                            ZStack {
                                Circle()
                                    .fill(BrandConfig.brand.opacity(0.12))
                                    .frame(width: 54, height: 54)
                                Text(String(user.name.prefix(1)).uppercased())
                                    .font(.title2).fontWeight(.bold)
                                    .foregroundStyle(BrandConfig.brand)
                            }
                            VStack(alignment: .leading, spacing: 3) {
                                Text(user.name).fontWeight(.semibold)
                                Text(user.email).font(.caption).foregroundStyle(.secondary)
                            }
                        }
                        .padding(.vertical, 4)

                        // Credits balance row
                        NavigationLink { CreditsShopView() } label: {
                            HStack {
                                Label(lang.t("クレジット残高", en: "Credits", zh: "点数余额", ko: "크레딧 잔액"),
                                      systemImage: "bolt.fill")
                                Spacer()
                                Text("\(user.creditBalance)")
                                    .fontWeight(.bold)
                                    .foregroundStyle(BrandConfig.brand)
                            }
                        }
                    }
                }

                // MARK: 連携
                Section(lang.t("連携", en: "Integrations", zh: "集成", ko: "연동")) {
                    NavigationLink {
                        ConnectorsView()
                    } label: {
                        Label(lang.t("コネクター", en: "Connectors", zh: "连接器", ko: "커넥터"),
                              systemImage: "link.circle.fill")
                    }
                }

                // MARK: ツール
                Section(lang.t("ツール", en: "Tools", zh: "工具", ko: "도구")) {
                    NavigationLink {
                        CronTasksView()
                    } label: {
                        Label(lang.t("定時タスク", en: "Cron Tasks", zh: "定时任务", ko: "크론 작업"),
                              systemImage: "clock.badge.checkmark.fill")
                    }

                    // Installed plugins per agent
                    if !agentService.agents.isEmpty {
                        ForEach(agentService.agents) { agent in
                            NavigationLink {
                                InstalledPluginsView(agent: agent)
                            } label: {
                                Label(
                                    lang.t("インストール済みプラグイン", en: "Installed Plugins", zh: "已安装插件", ko: "설치된 플러그인")
                                    + " — " + agent.name,
                                    systemImage: "puzzlepiece.extension"
                                )
                            }
                        }
                    }
                }

                // MARK: 安全
                Section(lang.t("安全", en: "Security", zh: "安全", ko: "보안")) {
                    Toggle(isOn: $envProtection) {
                        VStack(alignment: .leading, spacing: 2) {
                            HStack(spacing: 6) {
                                Text(lang.t("PC環境保護", en: "Environment Protection", zh: "环境保护", ko: "환경 보호"))
                                    .font(.subheadline).fontWeight(.medium)
                                SecurityBadge(label: lang.t("Active Defense", en: "Active Defense", zh: "主动防御", ko: "능동 방어"),
                                              color: BrandConfig.brand)
                            }
                            Text(lang.t(
                                "エージェントがタスクを実行する際、フルプロセスのセキュリティ制御を適用",
                                en: "Full-process security controls when an agent executes tasks",
                                zh: "代理执行任务时应用完整的安全控制",
                                ko: "에이전트가 작업을 실행할 때 전체 프로세스 보안 제어 적용"
                            ))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        }
                    }
                    .tint(BrandConfig.brand)

                    Toggle(isOn: $dataProtection) {
                        VStack(alignment: .leading, spacing: 2) {
                            HStack(spacing: 6) {
                                Text(lang.t("ユーザーデータ保護", en: "User Data Protection", zh: "用户数据保护", ko: "사용자 데이터 보호"))
                                    .font(.subheadline).fontWeight(.medium)
                                SecurityBadge(label: lang.t("Smart Detection", en: "Smart Detection", zh: "智能检测", ko: "스마트 감지"),
                                              color: Color(UIColor.systemBlue))
                            }
                            Text(lang.t(
                                "エージェントに送信されるデータを自動スキャンして個人情報を検出",
                                en: "Automatically scans data sent to agents to detect personal information",
                                zh: "自动扫描发送给代理的数据以检测个人信息",
                                ko: "에이전트로 전송되는 데이터를 자동으로 스캔하여 개인 정보 감지"
                            ))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        }
                    }
                    .tint(BrandConfig.brand)

                    Toggle(isOn: $skillScan) {
                        VStack(alignment: .leading, spacing: 2) {
                            HStack(spacing: 6) {
                                Text(lang.t("スキルセキュリティスキャン", en: "Skill Security Scan", zh: "技能安全扫描", ko: "스킬 보안 스캔"))
                                    .font(.subheadline).fontWeight(.medium)
                                SecurityBadge(label: lang.t("Multi-layer Check", en: "Multi-layer Check", zh: "多层检查", ko: "다중 레이어 검사"),
                                              color: Color(UIColor.systemGreen))
                            }
                            Text(lang.t(
                                "スキルのインストール前にマルチレベルのセキュリティチェックを実行",
                                en: "Runs multi-level security checks before installing skills",
                                zh: "在安装技能之前运行多级安全检查",
                                ko: "스킬 설치 전에 다단계 보안 검사 실행"
                            ))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        }
                    }
                    .tint(BrandConfig.brand)
                }

                // MARK: 外観（言語 + テーマ）
                Section(lang.t("外観", en: "Appearance", zh: "外观", ko: "외관")) {
                    // Language picker
                    Picker(selection: Binding(
                        get: { lang.current },
                        set: { lang.current = $0 }
                    )) {
                        ForEach(AppLanguage.allCases) { language in
                            HStack {
                                Text(language.badge)
                                    .font(.caption.bold())
                                    .foregroundStyle(BrandConfig.brand)
                                    .frame(width: 28, height: 20)
                                    .background(BrandConfig.brand.opacity(0.10))
                                    .clipShape(RoundedRectangle(cornerRadius: 4))
                                Text(language.localName)
                            }
                            .tag(language.rawValue)
                        }
                    } label: {
                        Label(
                            AppLanguage(rawValue: lang.current)?.localName ?? "日本語",
                            systemImage: "globe"
                        )
                    }
                    .pickerStyle(.navigationLink)

                    // Theme picker
                    HStack {
                        Label(lang.t("テーマ", en: "Theme", zh: "主题", ko: "테마"),
                              systemImage: "circle.lefthalf.filled")
                        Spacer()
                        Picker("", selection: $colorScheme) {
                            Text(lang.t("自動", en: "Auto", zh: "自动", ko: "자동")).tag("system")
                            Image(systemName: "sun.max.fill").tag("light")
                            Image(systemName: "moon.fill").tag("dark")
                        }
                        .pickerStyle(.segmented)
                        .frame(width: 120)
                    }
                }

                // MARK: 関于
                Section(lang.t("関于", en: "About", zh: "关于", ko: "앱 정보")) {
                    HStack {
                        Label(lang.t("バージョン", en: "Version", zh: "版本", ko: "버전"),
                              systemImage: "info.circle")
                        Spacer()
                        Text("1.0.0")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Link(destination: URL(string: BrandConfig.privacyURL)!) {
                        Label(lang.t("プライバシーポリシー", en: "Privacy Policy", zh: "隐私政策", ko: "개인정보 처리방침"),
                              systemImage: "lock.shield")
                            .foregroundStyle(BrandConfig.brand)
                    }
                    Link(destination: URL(string: BrandConfig.termsURL)!) {
                        Label(lang.t("利用規約", en: "Terms of Service", zh: "使用条款", ko: "이용약관"),
                              systemImage: "doc.text")
                            .foregroundStyle(BrandConfig.brand)
                    }
                    Link(destination: URL(string: BrandConfig.privacyURL)!) {
                        Label(lang.t("\(BrandConfig.appName) を開く", en: "Open \(BrandConfig.appName)", zh: "打开 \(BrandConfig.appName)", ko: "\(BrandConfig.appName) 열기"),
                              systemImage: "safari")
                            .foregroundStyle(BrandConfig.brand)
                    }

                    // Data export
                    Button {
                        Task { await exportUserData() }
                    } label: {
                        HStack {
                            if isExporting {
                                ProgressView().padding(.trailing, 4)
                                Text(lang.t("エクスポート中...", en: "Exporting...", zh: "导出中...", ko: "내보내는 중..."))
                                    .foregroundStyle(.secondary)
                            } else {
                                Label(lang.t("データをエクスポート", en: "Export Data", zh: "导出数据", ko: "데이터 내보내기"),
                                      systemImage: "square.and.arrow.up")
                                    .foregroundStyle(BrandConfig.brand)
                            }
                        }
                    }
                    .disabled(isExporting)
                    .sheet(isPresented: $showExportShare) {
                        if let data = exportData {
                            ShareSheet(items: [data as Any])
                        }
                    }
                }

                // MARK: 危険ゾーン
                Section {
                    Text(lang.t(
                        "すべての操作はシステム保護下で実行されます",
                        en: "All operations run under system protection",
                        zh: "所有操作均在系统保护下运行",
                        ko: "모든 작업은 시스템 보호 하에 실행됩니다"
                    ))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .listRowBackground(Color.clear)

                    // Delete all data
                    Button(role: .destructive) {
                        showDeleteConfirm = true
                    } label: {
                        HStack {
                            Spacer()
                            if isDeletingData {
                                ProgressView().padding(.trailing, 4)
                            } else {
                                Label(lang.t("すべてのデータを削除", en: "Delete All Data", zh: "删除所有数据", ko: "모든 데이터 삭제"),
                                      systemImage: "trash.fill")
                            }
                            Spacer()
                        }
                    }
                    .disabled(isDeletingData)

                    // Logout
                    Button(role: .destructive) {
                        authManager.logout()
                    } label: {
                        HStack {
                            Spacer()
                            Label(lang.t("ログアウト", en: "Logout", zh: "退出登录", ko: "로그아웃"),
                                  systemImage: "rectangle.portrait.and.arrow.right")
                            Spacer()
                        }
                    }
                } header: {
                    Text(lang.t("危険ゾーン", en: "Danger Zone", zh: "危险区域", ko: "위험 구역"))
                }
            }
            .navigationTitle(lang.t("設定", en: "Settings", zh: "设置", ko: "설정"))
            .alert(lang.t("エラー", en: "Error", zh: "错误", ko: "오류"),
                   isPresented: Binding(get: { exportError != nil },
                                        set: { if !$0 { exportError = nil } })) {
                Button("OK") { exportError = nil }
            } message: {
                Text(exportError ?? "")
            }
            .alert(lang.t("エラー", en: "Error", zh: "错误", ko: "오류"),
                   isPresented: Binding(get: { deleteError != nil },
                                        set: { if !$0 { deleteError = nil } })) {
                Button("OK") { deleteError = nil }
            } message: {
                Text(deleteError ?? "")
            }
            .confirmationDialog(
                lang.t("本当に削除しますか？", en: "Are you sure?", zh: "确定要删除吗？", ko: "정말 삭제하시겠습니까?"),
                isPresented: $showDeleteConfirm,
                titleVisibility: .visible
            ) {
                Button(lang.t("すべてのデータを削除", en: "Delete All Data", zh: "删除所有数据", ko: "모든 데이터 삭제"),
                       role: .destructive) {
                    Task { await deleteAllData() }
                }
                Button(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소"), role: .cancel) {}
            } message: {
                Text(lang.t(
                    "本当に削除しますか？この操作は取り消せません",
                    en: "This action cannot be undone. All agents, conversations, and messages will be permanently deleted.",
                    zh: "此操作无法撤销。所有助手、对话和消息将被永久删除。",
                    ko: "이 작업은 취소할 수 없습니다. 모든 에이전트, 대화 및 메시지가 영구적으로 삭제됩니다."
                ))
            }
        }
    }

    // MARK: - Delete All Data

    private func deleteAllData() async {
        await MainActor.run { isDeletingData = true }
        defer { Task { @MainActor in isDeletingData = false } }

        guard let url = URL(string: Constants.baseURL + Constants.API.deleteAllUserData) else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "DELETE"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = KeychainHelper.shared.readString(for: Constants.accessTokenKey) {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        do {
            let (_, response) = try await URLSession.shared.data(for: req)
            if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                await MainActor.run { authManager.logout() }
            } else {
                await MainActor.run {
                    deleteError = lang.t("削除に失敗しました", en: "Failed to delete data", zh: "删除失败", ko: "데이터 삭제 실패")
                }
            }
        } catch {
            await MainActor.run { deleteError = error.localizedDescription }
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

// MARK: - Security badge

private struct SecurityBadge: View {
    let label: String
    let color: Color

    var body: some View {
        Text(label)
            .font(.caption2.bold())
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color.opacity(0.12))
            .foregroundStyle(color)
            .clipShape(Capsule())
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
