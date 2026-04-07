import SwiftUI

// MARK: - Models

enum CronFrequency: String, CaseIterable, Identifiable {
    case hourly, daily, weekly, monthly, custom
    var id: String { rawValue }

    func label(_ lang: LanguageManager) -> String {
        switch self {
        case .hourly:  return lang.t("毎時", en: "Hourly",  zh: "每小时", ko: "매시간")
        case .daily:   return lang.t("毎日", en: "Daily",   zh: "每天",   ko: "매일")
        case .weekly:  return lang.t("毎週", en: "Weekly",  zh: "每周",   ko: "매주")
        case .monthly: return lang.t("毎月", en: "Monthly", zh: "每月",   ko: "매월")
        case .custom:  return lang.t("カスタム", en: "Custom", zh: "自定义", ko: "사용자 정의")
        }
    }
}

enum CronTaskStatus {
    case running, paused, completed

    func label(_ lang: LanguageManager) -> String {
        switch self {
        case .running:   return lang.t("実行中", en: "Running",   zh: "运行中", ko: "실행 중")
        case .paused:    return lang.t("一時停止", en: "Paused",  zh: "已暂停", ko: "일시 중지")
        case .completed: return lang.t("完了",    en: "Completed", zh: "已完成", ko: "완료")
        }
    }

    var color: Color {
        switch self {
        case .running:   return .green
        case .paused:    return .orange
        case .completed: return .secondary
        }
    }
}

struct CronTask: Identifiable {
    let id = UUID()
    var name: String
    var taskDescription: String
    var frequency: CronFrequency
    var agentName: String
    var status: CronTaskStatus
    var createdAt: Date = .now
}

// MARK: - Step Card

private struct StepCard: View {
    let step: Int
    let title: String
    let description: String

    var body: some View {
        HStack(alignment: .top, spacing: 14) {
            ZStack {
                Circle()
                    .fill(BrandConfig.brand.opacity(0.12))
                    .frame(width: 36, height: 36)
                Text("\(step)")
                    .font(.subheadline.bold())
                    .foregroundStyle(BrandConfig.brand)
            }
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline).fontWeight(.semibold)
                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer()
        }
        .padding(14)
        .background(Color(.secondarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

// MARK: - Task Row

private struct TaskRowView: View {
    @Environment(\.lang) var lang
    let task: CronTask

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(task.name)
                    .font(.subheadline).fontWeight(.semibold)
                Spacer()
                Text(task.status.label(lang))
                    .font(.caption.bold())
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(task.status.color.opacity(0.15))
                    .foregroundStyle(task.status.color)
                    .clipShape(Capsule())
            }
            if !task.taskDescription.isEmpty {
                Text(task.taskDescription)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
            HStack(spacing: 12) {
                Label(task.frequency.label(lang), systemImage: "clock")
                Label(task.agentName, systemImage: "cpu")
            }
            .font(.caption2)
            .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Create Sheet

private struct CreateCronTaskSheet: View {
    @Environment(\.dismiss) var dismiss
    @Environment(\.lang) var lang
    @Environment(AgentService.self) var agentService

    @Binding var tasks: [CronTask]

    @State private var name = ""
    @State private var taskDescription = ""
    @State private var frequency: CronFrequency = .daily
    @State private var selectedAgentIndex = 0
    @State private var showComingSoon = false

    var body: some View {
        NavigationStack {
            Form {
                Section(lang.t("タスク情報", en: "Task Info", zh: "任务信息", ko: "작업 정보")) {
                    TextField(lang.t("タスク名", en: "Task name", zh: "任务名称", ko: "작업 이름"), text: $name)
                    TextField(lang.t("AIへの指示（何をするか）", en: "Instructions for AI (what to do)", zh: "AI指令（做什么）", ko: "AI 지시사항 (무엇을 할지)"), text: $taskDescription, axis: .vertical)
                        .lineLimit(3...6)
                }

                Section(lang.t("実行頻度", en: "Frequency", zh: "执行频率", ko: "실행 빈도")) {
                    Picker(lang.t("頻度", en: "Frequency", zh: "频率", ko: "빈도"), selection: $frequency) {
                        ForEach(CronFrequency.allCases) { f in
                            Text(f.label(lang)).tag(f)
                        }
                    }
                    .pickerStyle(.segmented)
                }

                if !agentService.agents.isEmpty {
                    Section(lang.t("エージェント", en: "Agent", zh: "助手", ko: "에이전트")) {
                        Picker(lang.t("エージェントを選択", en: "Select agent", zh: "选择助手", ko: "에이전트 선택"), selection: $selectedAgentIndex) {
                            ForEach(agentService.agents.indices, id: \.self) { i in
                                Text(agentService.agents[i].name).tag(i)
                            }
                        }
                    }
                }

                Section {
                    HStack {
                        Image(systemName: "info.circle")
                            .foregroundStyle(.secondary)
                        Text(lang.t("バックエンドAPIは現在開発中です。タスクは保存されますが実行されません。", en: "Backend API is in development. Tasks are saved locally but not executed.", zh: "后端API正在开发中。任务将本地保存但不会执行。", ko: "백엔드 API가 개발 중입니다. 작업은 로컬에 저장되지만 실행되지 않습니다."))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle(lang.t("タスクを作成", en: "Create Task", zh: "创建任务", ko: "작업 만들기"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소")) { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(lang.t("作成", en: "Create", zh: "创建", ko: "만들기")) {
                        createTask()
                    }
                    .disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }

    private func createTask() {
        let agentName = agentService.agents.isEmpty
            ? lang.t("未選択", en: "None", zh: "未选择", ko: "없음")
            : agentService.agents[selectedAgentIndex].name
        let task = CronTask(
            name: name.trimmingCharacters(in: .whitespaces),
            taskDescription: taskDescription,
            frequency: frequency,
            agentName: agentName,
            status: .paused
        )
        tasks.append(task)
        dismiss()
    }
}

// MARK: - CronTasksView

struct CronTasksView: View {
    @Environment(\.lang) var lang
    @State private var tasks: [CronTask] = []
    @State private var showCreateSheet = false

    var body: some View {
        Group {
            if tasks.isEmpty {
                emptyState
            } else {
                List {
                    ForEach(tasks) { task in
                        TaskRowView(task: task)
                    }
                    .onDelete { tasks.remove(atOffsets: $0) }
                }
            }
        }
        .navigationTitle(lang.t("定時タスク", en: "Cron Tasks", zh: "定时任务", ko: "크론 작업"))
        .navigationBarTitleDisplayMode(.large)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    showCreateSheet = true
                } label: {
                    Image(systemName: "plus")
                        .fontWeight(.semibold)
                }
            }
        }
        .sheet(isPresented: $showCreateSheet) {
            CreateCronTaskSheet(tasks: $tasks)
        }
    }

    // MARK: Empty State

    private var emptyState: some View {
        ScrollView {
            VStack(spacing: 28) {
                Spacer(minLength: 32)

                ZStack {
                    Circle()
                        .fill(BrandConfig.brand.opacity(0.10))
                        .frame(width: 96, height: 96)
                    Image(systemName: "clock.badge.checkmark.fill")
                        .font(.system(size: 42))
                        .foregroundStyle(BrandConfig.brand)
                }

                VStack(spacing: 8) {
                    Text(lang.t("初めてのタスクを作成", en: "Create your first task", zh: "创建您的第一个任务", ko: "첫 번째 작업 만들기"))
                        .font(.title2).fontWeight(.bold)
                    Text(lang.t(
                        "AIエージェントにスケジュールタスクを自動実行させましょう",
                        en: "Let your AI agent run scheduled tasks automatically",
                        zh: "让AI助手按计划自动执行任务",
                        ko: "AI 에이전트가 예약된 작업을 자동으로 실행하도록 하세요"
                    ))
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)
                }

                VStack(spacing: 12) {
                    StepCard(
                        step: 1,
                        title: lang.t("シナリオを想像する", en: "Imagine a scenario", zh: "想象使用场景", ko: "시나리오를 상상하세요"),
                        description: lang.t(
                            "毎日のレポート、定期的な通知、自動データ収集など",
                            en: "Daily reports, periodic notifications, automated data collection, and more",
                            zh: "每日报告、定期通知、自动数据收集等",
                            ko: "일일 보고서, 정기 알림, 자동 데이터 수집 등"
                        )
                    )
                    StepCard(
                        step: 2,
                        title: lang.t("頻度を設定する", en: "Set the frequency", zh: "设置执行频率", ko: "빈도를 설정하세요"),
                        description: lang.t(
                            "毎時・毎日・毎週・毎月、またはカスタムスケジュール",
                            en: "Hourly, daily, weekly, monthly, or a custom schedule",
                            zh: "每小时、每天、每周、每月或自定义计划",
                            ko: "매시간, 매일, 매주, 매월 또는 사용자 정의 일정"
                        )
                    )
                    StepCard(
                        step: 3,
                        title: lang.t("自動で実行される", en: "It runs automatically", zh: "自动执行", ko: "자동으로 실행됩니다"),
                        description: lang.t(
                            "設定したスケジュールでエージェントが自動的にタスクを実行します",
                            en: "Your agent automatically executes the task on the set schedule",
                            zh: "代理按照设定的计划自动执行任务",
                            ko: "에이전트가 설정된 일정에 따라 자동으로 작업을 실행합니다"
                        )
                    )
                }
                .padding(.horizontal)

                Button {
                    showCreateSheet = true
                } label: {
                    Text(lang.t("+ 作成", en: "+ Create", zh: "+ 创建", ko: "+ 만들기"))
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                        .background(BrandConfig.brand)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                .padding(.horizontal)

                Spacer(minLength: 32)
            }
        }
    }
}
