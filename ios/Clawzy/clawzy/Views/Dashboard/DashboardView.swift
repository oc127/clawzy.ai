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
            .navigationTitle(lang.t("ホーム", en: "Home", zh: "首页", ko: "홈"))
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    StatusBadge(status: healthMonitor.overallStatus) {
                        showHealthDetail = true
                    }
                }
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showCreateAgent = true
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .foregroundStyle(BrandConfig.brand)
                            .font(.title3)
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

    private var agentList: some View {
        ScrollView {
            VStack(spacing: 0) {
                // Credits header card
                if let user = authManager.currentUser {
                    CreditsCard(balance: user.creditBalance)
                        .padding(.horizontal, 16)
                        .padding(.top, 16)
                        .padding(.bottom, 14)
                }

                // Section header
                HStack {
                    Text(lang.t("マイエージェント", en: "MY AGENTS", zh: "我的助手", ko: "내 에이전트"))
                        .font(.footnote)
                        .fontWeight(.semibold)
                        .foregroundStyle(.secondary)
                        .textCase(.uppercase)
                    Spacer()
                    Text(lang.current == "en"
                         ? "\(agentService.agents.count)"
                         : "\(agentService.agents.count)\(lang.t("体", zh: "个", ko: "개"))")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 10)

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
            .padding(.bottom, 24)
        }
        .background(BrandConfig.backgroundColor)
    }
}

// MARK: - Status badge

private struct StatusBadge: View {
    let status: ServiceStatus
    let onTap: () -> Void

    private var color: Color {
        switch status {
        case .online:   return .green
        case .degraded: return .yellow
        case .offline:  return .red
        }
    }

    var body: some View {
        Button(action: onTap) {
            Circle()
                .fill(color)
                .frame(width: 10, height: 10)
                .shadow(color: color.opacity(0.6), radius: 3)
        }
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

// MARK: - Credits card

private struct CreditsCard: View {
    let balance: Int
    @Environment(\.lang) var lang
    @State private var showShop = false

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(lang.t("クレジット残高", en: "Credit Balance", zh: "点数余额", ko: "크레딧 잔액"))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text("\(balance)")
                    .font(.title)
                    .fontWeight(.bold)
                    .foregroundStyle(BrandConfig.brand)
            }
            Spacer()
            Button { showShop = true } label: {
                ZStack {
                    Circle()
                        .fill(BrandConfig.brand.opacity(0.10))
                        .frame(width: 52, height: 52)
                    Image(systemName: "bolt.fill")
                        .font(.title3)
                        .foregroundStyle(BrandConfig.brand)
                }
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(BrandConfig.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.04), radius: 4, y: 2)
        .sheet(isPresented: $showShop) { CreditsShopView() }
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
        case .running:  return .green
        case .creating: return .yellow
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

    /// True if the agent was created within the last 24 hours.
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
            ZStack {
                Circle()
                    .fill(BrandConfig.brand)
                    .frame(width: 36, height: 36)
                Text("N")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundStyle(.white)
            }
            .frame(width: 42, height: 42)

            VStack(alignment: .leading, spacing: 4) {
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
                    .frame(width: 8, height: 8)
                Text(statusLabel)
                    .font(.caption)
                    .foregroundStyle(statusColor)
            }
            .padding(.horizontal, 9)
            .padding(.vertical, 5)
            .background(statusColor.opacity(0.10))
            .clipShape(Capsule())

            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(Color(UIColor.systemGray3))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
        .background(BrandConfig.cardBackground)
    }
}
