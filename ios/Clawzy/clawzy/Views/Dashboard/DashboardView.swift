import SwiftUI

struct DashboardView: View {
    @Environment(AuthManager.self) var authManager
    @Environment(AgentService.self) var agentService
    @Environment(HealthMonitor.self) var healthMonitor
    @Environment(\.lang) var lang
    @State private var showCreateAgent = false
    @State private var showHealthDetail = false

    var body: some View {
        NavigationStack {
            ZStack(alignment: .bottomTrailing) {
                Group {
                    if agentService.isLoading && agentService.agents.isEmpty {
                        ProgressView(lang.t("読み込み中...", en: "Loading...", zh: "加载中...", ko: "로딩 중..."))
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else if agentService.agents.isEmpty {
                        EmptyAgentView { showCreateAgent = true }
                    } else {
                        agentList
                    }
                }

                // Floating create button
                if !agentService.agents.isEmpty {
                    Button {
                        showCreateAgent = true
                    } label: {
                        Image(systemName: "plus")
                            .font(.system(size: 20, weight: .semibold))
                            .foregroundStyle(.white)
                            .frame(width: 56, height: 56)
                            .background(BrandConfig.brand)
                            .clipShape(Circle())
                            .shadow(color: BrandConfig.brand.opacity(0.35), radius: 10, y: 4)
                    }
                    .padding(.trailing, 20)
                    .padding(.bottom, 20)
                    .accessibilityLabel(lang.t("エージェントを作成", en: "Create Agent", zh: "创建助手", ko: "에이전트 만들기"))
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                // Leading: N Logo + App Name (taps to open health detail)
                ToolbarItem(placement: .navigationBarLeading) {
                    Button { showHealthDetail = true } label: {
                        HStack(spacing: 8) {
                            NipponLogo(size: 28)
                            Text("NipponClaw")
                                .font(.headline)
                                .foregroundStyle(.primary)
                        }
                    }
                    .buttonStyle(.plain)
                }

                // Trailing: health dot + credits badge
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: 8) {
                        // Health status dot
                        Circle()
                            .fill(healthDotColor)
                            .frame(width: 8, height: 8)
                            .shadow(color: healthDotColor.opacity(0.5), radius: 3)

                        // Credits badge
                        if let user = authManager.currentUser {
                            NavigationLink {
                                CreditsShopView()
                            } label: {
                                HStack(spacing: 3) {
                                    Image(systemName: "bolt.fill")
                                        .font(.caption2)
                                    Text("\(user.creditBalance)")
                                        .font(.caption)
                                        .fontWeight(.semibold)
                                }
                                .foregroundStyle(BrandConfig.brand)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(BrandConfig.brand.opacity(0.10))
                                .clipShape(Capsule())
                            }
                        }
                    }
                }
            }
            .sheet(isPresented: $showCreateAgent) {
                CreateAgentView(agentService: agentService)
            }
            .sheet(isPresented: $showHealthDetail) {
                HealthDetailSheet(healthMonitor: healthMonitor)
            }
            .task { await agentService.fetchAgents() }
            .refreshable { await agentService.fetchAgents() }
        }
    }

    private var healthDotColor: Color {
        switch healthMonitor.overallStatus {
        case .online:   return Color(UIColor.systemGreen)
        case .degraded: return Color(UIColor.systemOrange)
        case .offline:  return Color(UIColor.systemRed)
        }
    }

    private var agentList: some View {
        ScrollView {
            VStack(spacing: 0) {
                // Section header
                HStack {
                    Text(lang.t("マイエージェント", en: "MY AGENTS", zh: "我的助手", ko: "내 에이전트"))
                        .font(.footnote)
                        .fontWeight(.semibold)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text(lang.current == "en"
                         ? "\(agentService.agents.count)"
                         : "\(agentService.agents.count)\(lang.t("体", zh: "个", ko: "개"))")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
                .padding(.horizontal, 20)
                .padding(.top, 16)
                .padding(.bottom, 10)

                // Agent cards
                VStack(spacing: 1) {
                    ForEach(agentService.agents) { agent in
                        HStack(spacing: 0) {
                            NavigationLink {
                                ChatView(agent: agent)
                            } label: {
                                AgentRowView(agent: agent)
                            }
                            .buttonStyle(.plain)

                            NavigationLink {
                                AgentDetailView(agent: agent)
                            } label: {
                                Image(systemName: "gearshape")
                                    .font(.system(size: 15))
                                    .foregroundStyle(.secondary)
                                    .frame(width: 44, height: 44)
                            }
                            .buttonStyle(.plain)
                            .padding(.trailing, 4)
                            .background(BrandConfig.cardBackground)
                        }
                    }
                }
                .background(BrandConfig.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .padding(.horizontal, 16)
            }
            .padding(.bottom, 96) // space for floating FAB
        }
        .background(BrandConfig.backgroundColor)
    }
}

// MARK: - Health detail sheet

private struct HealthDetailSheet: View {
    let healthMonitor: HealthMonitor
    @Environment(\.dismiss) var dismiss
    @Environment(\.lang) var lang

    private var statusText: String {
        switch healthMonitor.overallStatus {
        case .online:   return lang.t("正常", en: "All Systems Online", zh: "一切正常", ko: "정상")
        case .degraded: return lang.t("OpenClaw 異常", en: "OpenClaw Degraded", zh: "OpenClaw 异常", ko: "OpenClaw 이상")
        case .offline:  return lang.t("オフライン", en: "Server Offline", zh: "服务器离线", ko: "서버 오프라인")
        }
    }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    HStack {
                        Label(lang.t("バックエンド", en: "Backend", zh: "后端", ko: "백엔드"),
                              systemImage: "server.rack")
                        Spacer()
                        Circle()
                            .fill(healthMonitor.isBackendOnline ? Color.green : Color.red)
                            .frame(width: 10, height: 10)
                        Text(healthMonitor.isBackendOnline
                             ? lang.t("オンライン", en: "Online", zh: "在线", ko: "온라인")
                             : lang.t("オフライン", en: "Offline", zh: "离线", ko: "오프라인"))
                            .foregroundStyle(healthMonitor.isBackendOnline ? .green : .red)
                            .font(.subheadline)
                    }
                    HStack {
                        Label("OpenClaw", systemImage: "cube.box")
                        Spacer()
                        Circle()
                            .fill(healthMonitor.isOpenClawOnline ? Color.green : Color.yellow)
                            .frame(width: 10, height: 10)
                        Text(healthMonitor.isOpenClawOnline
                             ? lang.t("正常", en: "Online", zh: "正常", ko: "정상")
                             : lang.t("オフライン", en: "Offline", zh: "离线", ko: "오프라인"))
                            .foregroundStyle(healthMonitor.isOpenClawOnline ? .green : .yellow)
                            .font(.subheadline)
                    }
                }
                if let checked = healthMonitor.lastChecked {
                    Section {
                        HStack {
                            Text(lang.t("最終確認", en: "Last Checked", zh: "最后检查", ko: "마지막 확인"))
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text(checked, style: .relative)
                                .font(.subheadline)
                        }
                    }
                }
                Section {
                    Button {
                        Task { await healthMonitor.checkHealth() }
                    } label: {
                        HStack {
                            Spacer()
                            if healthMonitor.isChecking {
                                ProgressView()
                            } else {
                                Label(lang.t("再確認", en: "Refresh", zh: "刷新", ko: "새로고침"),
                                      systemImage: "arrow.clockwise")
                            }
                            Spacer()
                        }
                    }
                    .foregroundStyle(BrandConfig.brand)
                }
            }
            .navigationTitle(statusText)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button(lang.t("閉じる", en: "Close", zh: "关闭", ko: "닫기")) { dismiss() }
                }
            }
        }
        .presentationDetents([.medium])
    }
}

// MARK: - Empty state

private struct EmptyAgentView: View {
    let onCreate: () -> Void
    @Environment(\.lang) var lang

    var body: some View {
        VStack(spacing: 20) {
            Spacer()
            ZStack {
                Circle()
                    .fill(BrandConfig.brand.opacity(0.08))
                    .frame(width: 88, height: 88)
                NipponLogo(size: 48)
            }
            VStack(spacing: 6) {
                Text(lang.t("エージェントがまだいません",
                            en: "No agents yet",
                            zh: "还没有助手",
                            ko: "에이전트가 없습니다"))
                    .font(.title3).fontWeight(.semibold)
                Text(lang.t("最初のAIエージェントを作成しましょう",
                            en: "Create your first AI agent",
                            zh: "来创建你的第一个AI助手吧",
                            ko: "첫 번째 AI 에이전트를 만들어보세요"))
                    .font(.subheadline).foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            BrandButton(title: lang.t("エージェントを作成", en: "Create Agent", zh: "创建助手", ko: "에이전트 만들기"),
                        isLoading: false, action: onCreate)
                .padding(.horizontal, 48).padding(.top, 8)
            Spacer()
        }
        .background(BrandConfig.backgroundColor)
    }
}

// MARK: - Agent row

struct AgentRowView: View {
    let agent: Agent
    @Environment(\.lang) var lang

    var statusColor: Color {
        switch agent.status {
        case .running:  return Color(UIColor.systemGreen)
        case .creating: return Color(UIColor.systemOrange)
        case .stopped:  return Color(UIColor.systemGray3)
        case .error:    return BrandConfig.brand
        }
    }

    var statusLabel: String {
        switch agent.status {
        case .running:  return lang.t("稼働中", en: "Active",   zh: "运行中", ko: "실행 중")
        case .creating: return lang.t("作成中", en: "Creating", zh: "创建中", ko: "생성 중")
        case .stopped:  return lang.t("停止中", en: "Stopped",  zh: "已停止", ko: "중지됨")
        case .error:    return lang.t("エラー", en: "Error",    zh: "错误",   ko: "오류")
        }
    }

    var isNew: Bool {
        let iso = ISO8601DateFormatter()
        iso.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = iso.date(from: agent.createdAt) {
            return Date.now.timeIntervalSince(date) < 86400
        }
        iso.formatOptions = [.withInternetDateTime]
        if let date = iso.date(from: agent.createdAt) {
            return Date.now.timeIntervalSince(date) < 86400
        }
        return false
    }

    var body: some View {
        HStack(spacing: 14) {
            // N avatar 36pt
            ZStack {
                Circle()
                    .fill(BrandConfig.brand)
                    .frame(width: 36, height: 36)
                Text("N")
                    .font(.system(size: 15, weight: .bold, design: .rounded))
                    .foregroundStyle(.white)
            }

            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 6) {
                    Text(agent.name)
                        .font(.headline)
                        .foregroundStyle(.primary)
                    if isNew {
                        Text(lang.t("新着", en: "NEW", zh: "新", ko: "NEW"))
                            .font(.caption2).fontWeight(.bold)
                            .foregroundStyle(.white)
                            .padding(.horizontal, 5).padding(.vertical, 2)
                            .background(BrandConfig.brand)
                            .clipShape(Capsule())
                    }
                }
                Text(agent.modelName)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            HStack(spacing: 5) {
                Circle()
                    .fill(statusColor)
                    .frame(width: 7, height: 7)
                Text(statusLabel)
                    .font(.caption)
                    .foregroundStyle(statusColor)
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(statusColor.opacity(0.10))
            .clipShape(Capsule())

            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(Color(UIColor.systemGray3))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 13)
        .background(BrandConfig.cardBackground)
    }
}
