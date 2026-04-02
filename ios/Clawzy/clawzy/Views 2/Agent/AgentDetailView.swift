import SwiftUI

struct AgentDetailView: View {
    let agent: Agent
    @Environment(AgentService.self) var agentService
    @Environment(\.lang) var lang
    @Environment(\.dismiss) var dismiss
    @State private var service = AgentDetailService()
    @State private var isStarting = false
    @State private var isStopping = false
    @State private var showDeleteConfirm = false
    @State private var currentAgent: Agent

    init(agent: Agent) {
        self.agent = agent
        self._currentAgent = State(initialValue: agent)
    }

    private var statusColor: Color {
        switch currentAgent.status {
        case .running:  return .green
        case .creating: return .yellow
        case .stopped:  return Color(UIColor.systemGray3)
        case .error:    return BrandConfig.brand
        }
    }

    private var statusLabel: String {
        switch currentAgent.status {
        case .running:  return lang.t("稼働中", en: "Running",  zh: "运行中", ko: "실행 중")
        case .creating: return lang.t("作成中", en: "Creating", zh: "创建中", ko: "생성 중")
        case .stopped:  return lang.t("停止中", en: "Stopped",  zh: "已停止", ko: "중지됨")
        case .error:    return lang.t("エラー", en: "Error",    zh: "错误",   ko: "오류")
        }
    }

    var body: some View {
        List {
            // MARK: - Status Section
            Section {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(currentAgent.name)
                            .font(.title2).fontWeight(.bold)
                        Text(currentAgent.modelName)
                            .font(.subheadline).foregroundStyle(.secondary)
                    }
                    Spacer()
                    HStack(spacing: 6) {
                        Circle().fill(statusColor).frame(width: 10, height: 10)
                        Text(statusLabel)
                            .font(.subheadline).foregroundStyle(statusColor)
                    }
                    .padding(.horizontal, 10).padding(.vertical, 6)
                    .background(statusColor.opacity(0.12))
                    .clipShape(Capsule())
                }

                HStack(spacing: 12) {
                    Button {
                        Task {
                            isStarting = true
                            await agentService.startAgent(currentAgent.id)
                            if let updated = agentService.agents.first(where: { $0.id == currentAgent.id }) {
                                currentAgent = updated
                            }
                            isStarting = false
                        }
                    } label: {
                        HStack {
                            if isStarting { ProgressView().tint(.white) }
                            else { Image(systemName: "play.fill") }
                            Text(lang.t("起動", en: "Start", zh: "启动", ko: "시작"))
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(currentAgent.status == .running ? Color.gray.opacity(0.3) : Color.green)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .disabled(currentAgent.status == .running || isStarting)

                    Button {
                        Task {
                            isStopping = true
                            await agentService.stopAgent(currentAgent.id)
                            if let updated = agentService.agents.first(where: { $0.id == currentAgent.id }) {
                                currentAgent = updated
                            }
                            isStopping = false
                        }
                    } label: {
                        HStack {
                            if isStopping { ProgressView().tint(.white) }
                            else { Image(systemName: "stop.fill") }
                            Text(lang.t("停止", en: "Stop", zh: "停止", ko: "중지"))
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(currentAgent.status == .stopped ? Color.gray.opacity(0.3) : BrandConfig.brand)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .disabled(currentAgent.status == .stopped || isStopping)
                }
                .buttonStyle(.plain)
            }

            // MARK: - Tools
            Section {
                NavigationLink {
                    ToolsView(agentId: currentAgent.id)
                } label: {
                    Label(lang.t("ツール", en: "Tools", zh: "工具", ko: "도구"),
                          systemImage: "wrench.and.screwdriver")
                    if !service.tools.isEmpty {
                        Spacer()
                        Text("\(service.tools.filter(\.enabled).count)/\(service.tools.count)")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
            }

            // MARK: - Memory
            Section {
                NavigationLink {
                    MemoryListView(agentId: currentAgent.id)
                } label: {
                    Label(lang.t("メモリ", en: "Memory", zh: "记忆", ko: "메모리"),
                          systemImage: "brain.head.profile")
                    if !service.memories.isEmpty {
                        Spacer()
                        Text("\(service.memories.count)")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
            }

            // MARK: - Skills
            Section {
                Label(lang.t("スキル", en: "Skills", zh: "技能", ko: "스킬"),
                      systemImage: "star.fill")
                if service.skills.isEmpty {
                    Text(lang.t("スキルなし", en: "No skills installed", zh: "无技能", ko: "스킬 없음"))
                        .font(.subheadline).foregroundStyle(.secondary)
                } else {
                    ForEach(service.skills) { skill in
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(skill.name).font(.subheadline)
                                Text(skill.description)
                                    .font(.caption).foregroundStyle(.secondary)
                                    .lineLimit(1)
                            }
                            Spacer()
                            if let version = skill.version {
                                Text("v\(version)")
                                    .font(.caption2).foregroundStyle(.tertiary)
                            }
                        }
                    }
                }
            }

            // MARK: - Scheduled Tasks
            Section {
                NavigationLink {
                    TasksView(agentId: currentAgent.id)
                } label: {
                    Label(lang.t("スケジュールタスク", en: "Scheduled Tasks", zh: "定时任务", ko: "예약 작업"),
                          systemImage: "clock.badge")
                    if !service.tasks.isEmpty {
                        Spacer()
                        Text("\(service.tasks.count)")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
            }

            // MARK: - Channels
            Section {
                NavigationLink {
                    ChannelsView(agentId: currentAgent.id)
                } label: {
                    Label(lang.t("チャンネル", en: "Channels", zh: "频道", ko: "채널"),
                          systemImage: "bubble.left.and.bubble.right")
                    if !service.channels.isEmpty {
                        Spacer()
                        Text("\(service.channels.count)")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
            }

            // MARK: - Danger Zone
            Section {
                Button(role: .destructive) {
                    showDeleteConfirm = true
                } label: {
                    HStack {
                        Spacer()
                        Label(lang.t("エージェントを削除", en: "Delete Agent", zh: "删除助手", ko: "에이전트 삭제"),
                              systemImage: "trash")
                        Spacer()
                    }
                }
            } header: {
                Text(lang.t("危険ゾーン", en: "Danger Zone", zh: "危险区域", ko: "위험 구역"))
                    .foregroundStyle(.red)
            }
        }
        .navigationTitle(lang.t("エージェント詳細", en: "Agent Detail", zh: "助手详情", ko: "에이전트 상세"))
        .navigationBarTitleDisplayMode(.inline)
        .task {
            async let t: () = service.fetchTools(agentId: currentAgent.id)
            async let m: () = service.fetchMemories(agentId: currentAgent.id)
            async let s: () = service.fetchSkills(agentId: currentAgent.id)
            async let tk: () = service.fetchTasks(agentId: currentAgent.id)
            async let c: () = service.fetchChannels(agentId: currentAgent.id)
            _ = await (t, m, s, tk, c)
        }
        .alert(
            lang.t("エージェントを削除しますか？", en: "Delete this agent?", zh: "确定删除助手？", ko: "에이전트를 삭제하시겠습니까?"),
            isPresented: $showDeleteConfirm
        ) {
            Button(lang.t("削除", en: "Delete", zh: "删除", ko: "삭제"), role: .destructive) {
                Task {
                    await agentService.deleteAgent(currentAgent.id)
                    dismiss()
                }
            }
            Button(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소"), role: .cancel) {}
        } message: {
            Text(lang.t("この操作は取り消せません。", en: "This action cannot be undone.", zh: "此操作不可撤销。", ko: "이 작업은 취소할 수 없습니다."))
        }
    }
}
