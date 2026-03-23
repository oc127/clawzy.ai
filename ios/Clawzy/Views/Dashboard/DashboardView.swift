import SwiftUI

struct DashboardView: View {
    @Environment(AuthManager.self) var authManager
    @State private var agentService = AgentService()
    @State private var showCreateAgent = false

    var body: some View {
        NavigationStack {
            Group {
                if agentService.isLoading && agentService.agents.isEmpty {
                    ProgressView("加载中...")
                } else if agentService.agents.isEmpty {
                    // 空状态
                    VStack(spacing: 16) {
                        Text("🦞")
                            .font(.system(size: 48))
                        Text("还没有 Agent")
                            .font(.title3)
                            .fontWeight(.medium)
                        Text("创建你的第一个 AI 龙虾吧")
                            .foregroundStyle(.secondary)
                        Button("创建 Agent") {
                            showCreateAgent = true
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.orange)
                    }
                } else {
                    List {
                        // 积分信息
                        if let user = authManager.currentUser {
                            Section {
                                HStack {
                                    Text("积分余额")
                                    Spacer()
                                    Text("\(user.creditBalance)")
                                        .fontWeight(.bold)
                                        .foregroundStyle(.orange)
                                }
                            }
                        }

                        // Agent 列表
                        Section("我的 Agents") {
                            ForEach(agentService.agents) { agent in
                                NavigationLink {
                                    ChatView(agent: agent)
                                } label: {
                                    AgentRowView(agent: agent)
                                }
                            }
                            .onDelete { indexSet in
                                Task {
                                    for index in indexSet {
                                        let agent = agentService.agents[index]
                                        await agentService.deleteAgent(agent.id)
                                    }
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Dashboard")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showCreateAgent = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showCreateAgent) {
                CreateAgentView(agentService: agentService)
            }
            .task {
                await agentService.fetchAgents()
            }
            .refreshable {
                await agentService.fetchAgents()
            }
        }
    }
}

// MARK: - Agent 行视图

struct AgentRowView: View {
    let agent: Agent

    var statusColor: Color {
        switch agent.status {
        case .running: return .green
        case .creating: return .yellow
        case .stopped: return .gray
        case .error: return .red
        }
    }

    var body: some View {
        HStack(spacing: 12) {
            // 状态指示灯
            Circle()
                .fill(statusColor)
                .frame(width: 10, height: 10)

            VStack(alignment: .leading, spacing: 4) {
                Text(agent.name)
                    .fontWeight(.medium)
                Text(agent.modelName)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Text(agent.status.rawValue)
                .font(.caption)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(statusColor.opacity(0.15))
                .foregroundStyle(statusColor)
                .clipShape(Capsule())
        }
        .padding(.vertical, 4)
    }
}
