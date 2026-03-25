import SwiftUI

struct DashboardView: View {
    @Environment(AuthManager.self) var authManager
    @Environment(AgentService.self) var agentService
    @Environment(\.lang) var lang
    @State private var showCreateAgent = false

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
                        .padding(.bottom, 8)
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
                        NavigationLink {
                            ChatView(agent: agent)
                        } label: {
                            AgentRowView(agent: agent)
                        }
                        .buttonStyle(.plain)
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

// MARK: - Credits card

private struct CreditsCard: View {
    let balance: Int
    @Environment(\.lang) var lang

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
            ZStack {
                Circle()
                    .fill(BrandConfig.brand.opacity(0.10))
                    .frame(width: 52, height: 52)
                Image(systemName: "bolt.fill")
                    .font(.title3)
                    .foregroundStyle(BrandConfig.brand)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(BrandConfig.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.04), radius: 4, y: 2)
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
        case .stopped:  return Color(white: 0.7)
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
                Text(agent.name)
                    .fontWeight(.medium)
                    .foregroundStyle(.primary)
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
            .padding(.horizontal, 9)
            .padding(.vertical, 5)
            .background(statusColor.opacity(0.10))
            .clipShape(Capsule())

            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(Color(white: 0.75))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
        .background(BrandConfig.cardBackground)
    }
}
