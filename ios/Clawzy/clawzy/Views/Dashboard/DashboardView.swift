import SwiftUI

// MARK: - DashboardView

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
                        .background(BrandConfig.darkBg)
                } else {
                    mainContent
                }
            }
            .navigationBarHidden(true)
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

    // MARK: - Main content

    private var mainContent: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                // Top bar: logo left, credits + status right
                HStack(spacing: BrandConfig.Spacing.md) {
                    NipponLogo(size: 28)
                    Spacer()
                    if let user = authManager.currentUser {
                        HStack(spacing: 4) {
                            Image(systemName: "bolt.fill")
                                .font(.system(size: 10, weight: .bold))
                            Text("\(user.creditBalance)")
                                .font(.caption).fontWeight(.semibold)
                        }
                        .foregroundStyle(BrandConfig.brand)
                        .padding(.horizontal, BrandConfig.Spacing.sm)
                        .padding(.vertical, 4)
                        .background(BrandConfig.brand.opacity(0.10))
                        .clipShape(Capsule())
                    }
                    StatusBadge(status: healthMonitor.overallStatus) {
                        showHealthDetail = true
                    }
                }
                .padding(.horizontal, BrandConfig.Spacing.lg)
                .padding(.top, BrandConfig.Spacing.lg)
                .padding(.bottom, BrandConfig.Spacing.sm)

                // Greeting
                VStack(alignment: .leading, spacing: 4) {
                    Text(lang.t("こんにちは 👋", en: "Hello 👋", zh: "你好 👋", ko: "안녕하세요 👋"))
                        .font(.title).fontWeight(.bold)
                        .foregroundStyle(.primary)
                    if let user = authManager.currentUser {
                        Text(user.name)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.horizontal, BrandConfig.Spacing.lg)
                .padding(.top, BrandConfig.Spacing.sm)
                .padding(.bottom, BrandConfig.Spacing.md)

                // Hero credits card
                if let user = authManager.currentUser {
                    HeroCreditsCard(balance: user.creditBalance)
                        .padding(.horizontal, BrandConfig.Spacing.lg)
                        .padding(.bottom, BrandConfig.Spacing.lg)
                }

                // Agent section header
                HStack(alignment: .center) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(lang.t("あなたのエージェント", en: "Your Agents", zh: "你的助手", ko: "나의 에이전트"))
                            .font(.title3).fontWeight(.bold)
                            .foregroundStyle(.primary)
                        if !agentService.agents.isEmpty {
                            Text(lang.current == "en"
                                 ? "\(agentService.agents.count) agents"
                                 : "\(agentService.agents.count)" + lang.t("体", zh: "个", ko: "개"))
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    Spacer()
                    Button {
                        showCreateAgent = true
                    } label: {
                        ZStack {
                            Circle()
                                .fill(Color.primary)
                                .frame(width: 36, height: 36)
                            Image(systemName: "plus")
                                .font(.system(size: 16, weight: .bold))
                                .foregroundStyle(BrandConfig.darkBg)
                        }
                    }
                    .accessibilityLabel(lang.t("エージェントを作成", en: "Create Agent", zh: "创建助手", ko: "에이전트 만들기"))
                }
                .padding(.horizontal, BrandConfig.Spacing.lg)
                .padding(.bottom, BrandConfig.Spacing.sm)

                // Agent cards or empty state
                if agentService.agents.isEmpty {
                    EmptyAgentSection { showCreateAgent = true }
                        .padding(.horizontal, BrandConfig.Spacing.lg)
                } else {
                    VStack(spacing: BrandConfig.Spacing.md) {
                        ForEach(agentService.agents) { agent in
                            AgentCard(agent: agent)
                        }
                    }
                    .padding(.horizontal, BrandConfig.Spacing.lg)
                }

                // Quick actions
                quickActionsSection
                    .padding(.top, BrandConfig.Spacing.lg)
                    .padding(.bottom, BrandConfig.Spacing.xl)
            }
        }
        .background(BrandConfig.darkBg)
    }

    // MARK: - Quick actions

    private var quickActionsSection: some View {
        VStack(alignment: .leading, spacing: BrandConfig.Spacing.md) {
            Text(lang.t("クイックアクション", en: "Quick Actions", zh: "快速操作", ko: "빠른 실행"))
                .font(.title3).fontWeight(.bold)
                .padding(.horizontal, BrandConfig.Spacing.lg)

            LazyVGrid(
                columns: [
                    GridItem(.flexible(), spacing: BrandConfig.Spacing.md),
                    GridItem(.flexible(), spacing: BrandConfig.Spacing.md)
                ],
                spacing: BrandConfig.Spacing.md
            ) {
                QuickActionTile(
                    icon: "plus.bubble.fill",
                    label: lang.t("新規作成", en: "New Agent", zh: "新建助手", ko: "새 에이전트")
                ) { showCreateAgent = true }

                QuickActionTile(
                    icon: "storefront.fill",
                    label: lang.t("マーケット", en: "Market", zh: "市场", ko: "마켓")
                ) { }

                QuickActionTile(
                    icon: "bolt.fill",
                    label: lang.t("クレジット", en: "Credits", zh: "点数", ko: "크레딧")
                ) { }

                QuickActionTile(
                    icon: "gearshape.fill",
                    label: lang.t("設定", en: "Settings", zh: "设置", ko: "설정")
                ) { }
            }
            .padding(.horizontal, BrandConfig.Spacing.lg)
        }
    }
}

// MARK: - Hero Credits Card

private struct HeroCreditsCard: View {
    let balance: Int
    @Environment(\.lang) var lang
    @State private var showShop = false

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 8) {
                Text(lang.t("クレジット残高", en: "Credit Balance", zh: "点数余额", ko: "크레딧 잔액"))
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.85))
                HStack(alignment: .firstTextBaseline, spacing: 4) {
                    Text("\(balance)")
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundStyle(.white)
                    Text("pts")
                        .font(.subheadline).fontWeight(.medium)
                        .foregroundStyle(.white.opacity(0.75))
                }
                Text(balance > 100
                     ? lang.t("残高十分 ✓", en: "Good to go ✓", zh: "余额充足 ✓", ko: "잔액 충분 ✓")
                     : lang.t("残高少ない", en: "Low balance", zh: "余额不足", ko: "잔액 부족"))
                    .font(.caption).fontWeight(.medium)
                    .foregroundStyle(.white.opacity(0.80))
            }
            Spacer()
            Button { showShop = true } label: {
                VStack(spacing: 6) {
                    ZStack {
                        Circle()
                            .fill(.white.opacity(0.20))
                            .frame(width: 44, height: 44)
                        Image(systemName: "bolt.fill")
                            .font(.headline)
                            .foregroundStyle(.white)
                    }
                    Text(lang.t("チャージ", en: "Top Up", zh: "充值", ko: "충전"))
                        .font(.caption2).fontWeight(.semibold)
                        .foregroundStyle(.white.opacity(0.90))
                }
            }
        }
        .padding(.horizontal, BrandConfig.Spacing.xl)
        .padding(.vertical, 14)
        .background(
            LinearGradient(
                colors: [BrandConfig.brand, BrandConfig.brandDeep],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(color: BrandConfig.brand.opacity(0.35), radius: 12, x: 0, y: 6)
        .sheet(isPresented: $showShop) { CreditsShopView() }
    }
}

// MARK: - Agent Card

private struct AgentCard: View {
    let agent: Agent
    @Environment(\.lang) var lang

    var statusColor: Color {
        switch agent.status {
        case .running:  return Color(UIColor.systemGreen)
        case .creating: return Color(UIColor.systemYellow)
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

    var agentEmoji: String {
        let name = agent.name.lowercased()
        if name.contains("ビジネス") || name.contains("business") || name.contains("商") { return "💼" }
        if name.contains("コード") || name.contains("code") || name.contains("dev") { return "💻" }
        if name.contains("翻訳") || name.contains("translat") || name.contains("lang") { return "🌐" }
        if name.contains("デザイン") || name.contains("design") || name.contains("art") { return "🎨" }
        if name.contains("データ") || name.contains("data") || name.contains("anal") { return "📊" }
        if name.contains("リサーチ") || name.contains("research") { return "🔍" }
        if name.contains("教") || name.contains("tutor") || name.contains("learn") { return "📚" }
        if name.contains("ライター") || name.contains("writ") || name.contains("copy") { return "✍️" }
        return "🤖"
    }

    var body: some View {
        HStack(spacing: 0) {
            NavigationLink {
                ChatView(agent: agent)
            } label: {
                HStack(spacing: BrandConfig.Spacing.md) {
                    // Emoji icon with subtle brand bg
                    ZStack {
                        RoundedRectangle(cornerRadius: BrandConfig.Spacing.md)
                            .fill(BrandConfig.brand.opacity(0.08))
                            .frame(width: 52, height: 52)
                        Text(agentEmoji)
                            .font(.system(size: 28))
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text(agent.name)
                            .font(.callout).fontWeight(.semibold)
                            .foregroundStyle(.primary)
                            .lineLimit(1)
                        Text(agent.modelName)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                        HStack(spacing: 4) {
                            Circle()
                                .fill(statusColor)
                                .frame(width: 6, height: 6)
                            Text(statusLabel)
                                .font(.caption2).fontWeight(.medium)
                                .foregroundStyle(statusColor)
                        }
                        .padding(.horizontal, BrandConfig.Spacing.sm)
                        .padding(.vertical, 3)
                        .background(statusColor.opacity(0.10))
                        .clipShape(Capsule())
                    }

                    Spacer()

                    Image(systemName: "chevron.right")
                        .font(.caption).fontWeight(.semibold)
                        .foregroundStyle(.secondary)
                }
                .padding(.horizontal, BrandConfig.Spacing.lg)
                .padding(.vertical, BrandConfig.Spacing.md)
            }
            .buttonStyle(.plain)

            // Settings button
            NavigationLink {
                AgentDetailView(agent: agent)
            } label: {
                Image(systemName: "gearshape.fill")
                    .font(.system(size: 14))
                    .foregroundStyle(Color(UIColor.secondaryLabel))
                    .frame(width: 40, height: 40)
                    .background(BrandConfig.darkSurface)
                    .clipShape(RoundedRectangle(cornerRadius: BrandConfig.Spacing.md))
                    .padding(.trailing, BrandConfig.Spacing.md)
            }
            .buttonStyle(.plain)
        }
        .background(BrandConfig.darkCard)
        .clipShape(RoundedRectangle(cornerRadius: BrandConfig.Radius.card))
        .overlay(
            RoundedRectangle(cornerRadius: BrandConfig.Radius.card)
                .stroke(BrandConfig.darkSeparator, lineWidth: 1)
        )
    }
}

// MARK: - Quick Action Tile

private struct QuickActionTile: View {
    let icon: String
    let label: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: BrandConfig.Spacing.md) {
                ZStack {
                    RoundedRectangle(cornerRadius: BrandConfig.Radius.card)
                        .fill(BrandConfig.brand.opacity(0.10))
                        .frame(width: 52, height: 52)
                    Image(systemName: icon)
                        .font(.system(size: 22))
                        .foregroundStyle(BrandConfig.brand)
                }
                Text(label)
                    .font(.caption).fontWeight(.semibold)
                    .foregroundStyle(.primary)
                    .multilineTextAlignment(.center)
                    .lineLimit(2)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, BrandConfig.Spacing.lg)
            .padding(.horizontal, BrandConfig.Spacing.sm)
            .background(BrandConfig.darkCard)
            .clipShape(RoundedRectangle(cornerRadius: BrandConfig.Radius.card))
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Empty agent section

private struct EmptyAgentSection: View {
    let onCreate: () -> Void
    @Environment(\.lang) var lang

    var body: some View {
        VStack(spacing: BrandConfig.Spacing.lg) {
            ZStack {
                Circle()
                    .fill(BrandConfig.brand.opacity(0.08))
                    .frame(width: 72, height: 72)
                Text("🤖").font(.system(size: 36))
            }
            VStack(spacing: 6) {
                Text(lang.t("エージェントがまだいません",
                            en: "No agents yet",
                            zh: "还没有助手",
                            ko: "에이전트가 없습니다"))
                    .font(.headline).fontWeight(.semibold)
                Text(lang.t("最初のAIエージェントを作成しましょう",
                            en: "Create your first AI agent",
                            zh: "来创建你的第一个AI助手吧",
                            ko: "첫 번째 AI 에이전트를 만들어보세요"))
                    .font(.subheadline).foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            BrandButton(
                title: lang.t("エージェントを作成", en: "Create Agent", zh: "创建助手", ko: "에이전트 만들기"),
                isLoading: false,
                action: onCreate
            )
        }
        .padding(BrandConfig.Spacing.xl)
        .frame(maxWidth: .infinity)
        .background(BrandConfig.darkCard)
        .clipShape(RoundedRectangle(cornerRadius: BrandConfig.Radius.card))
    }
}

// MARK: - Status badge

private struct StatusBadge: View {
    let status: ServiceStatus
    let onTap: () -> Void

    private var color: Color {
        switch status {
        case .online:   return Color(UIColor.systemGreen)
        case .degraded: return Color(UIColor.systemYellow)
        case .offline:  return Color(UIColor.systemRed)
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
                            .fill(healthMonitor.isBackendOnline ? Color(UIColor.systemGreen) : Color(UIColor.systemRed))
                            .frame(width: 10, height: 10)
                        Text(healthMonitor.isBackendOnline
                             ? lang.t("オンライン", en: "Online", zh: "在线", ko: "온라인")
                             : lang.t("オフライン", en: "Offline", zh: "离线", ko: "오프라인"))
                            .foregroundStyle(healthMonitor.isBackendOnline ? Color(UIColor.systemGreen) : Color(UIColor.systemRed))
                            .font(.subheadline)
                    }
                    HStack {
                        Label("OpenClaw", systemImage: "cube.box")
                        Spacer()
                        Circle()
                            .fill(healthMonitor.isOpenClawOnline ? Color(UIColor.systemGreen) : Color(UIColor.systemYellow))
                            .frame(width: 10, height: 10)
                        Text(healthMonitor.isOpenClawOnline
                             ? lang.t("正常", en: "Online", zh: "正常", ko: "정상")
                             : lang.t("オフライン", en: "Offline", zh: "离线", ko: "오프라인"))
                            .foregroundStyle(healthMonitor.isOpenClawOnline ? Color(UIColor.systemGreen) : Color(UIColor.systemYellow))
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

// MARK: - AgentRowView (kept for backward compatibility)

struct AgentRowView: View {
    let agent: Agent
    @Environment(\.lang) var lang

    var statusColor: Color {
        switch agent.status {
        case .running:  return Color(UIColor.systemGreen)
        case .creating: return Color(UIColor.systemYellow)
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
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(BrandConfig.brand.opacity(0.10))
                    .frame(width: 42, height: 42)
                Text("🤖")
                    .font(.title3)
            }
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 6) {
                    Text(agent.name)
                        .fontWeight(.medium)
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
            .padding(.horizontal, 9).padding(.vertical, 5)
            .background(statusColor.opacity(0.10))
            .clipShape(Capsule())
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(Color(UIColor.systemGray3))
        }
        .padding(.horizontal, 16).padding(.vertical, 14)
        .background(BrandConfig.cardBackground)
    }
}
