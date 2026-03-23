import SwiftUI

struct DashboardView: View {
    @Environment(AuthManager.self) var authManager
    @State private var agentService = AgentService()
    @State private var showCreateAgent = false

    var body: some View {
        NavigationStack {
            Group {
                if agentService.isLoading && agentService.agents.isEmpty {
                    ProgressView("読み込み中...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if agentService.agents.isEmpty {
                    EmptyAgentView { showCreateAgent = true }
                } else {
                    agentList
                }
            }
            .navigationTitle("ホーム")
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
                    Text("マイエージェント")
                        .font(.footnote)
                        .fontWeight(.semibold)
                        .foregroundStyle(.secondary)
                        .textCase(.uppercase)
                    Spacer()
                    Text("\(agentService.agents.count)体")
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
                .background(Color.white)
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

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("クレジット残高")
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
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.04), radius: 4, y: 2)
    }
}

// MARK: - Empty state

private struct EmptyAgentView: View {
    let onCreate: () -> Void

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
                Text("エージェントがまだいません")
                    .font(.title3)
                    .fontWeight(.semibold)
                Text("最初のAIエージェントを作成しましょう")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            BrandButton(title: "エージェントを作成", isLoading: false, action: onCreate)
                .padding(.horizontal, 48)
                .padding(.top, 8)
            Spacer()
        }
        .background(BrandConfig.backgroundColor)
    }
}

// MARK: - Agent row

struct AgentRowView: View {
    let agent: Agent

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
        case .running:  return "稼働中"
        case .creating: return "作成中"
        case .stopped:  return "停止中"
        case .error:    return "エラー"
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
        .background(Color.white)
    }
}
