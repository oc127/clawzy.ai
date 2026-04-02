import SwiftUI

struct TasksView: View {
    let agentId: String
    @State private var service = AgentDetailService()
    @State private var showAddTask = false
    @Environment(\.lang) var lang

    var body: some View {
        Group {
            if service.isLoading && service.tasks.isEmpty {
                ProgressView(lang.t("読み込み中...", en: "Loading...", zh: "加载中...", ko: "로딩 중..."))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if service.tasks.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "clock.badge")
                        .font(.largeTitle)
                        .foregroundStyle(.secondary)
                    Text(lang.t("タスクがありません", en: "No scheduled tasks", zh: "暂无定时任务", ko: "예약된 작업이 없습니다"))
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List {
                    ForEach(service.tasks) { task in
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(task.cronExpression)
                                    .font(.caption).fontDesign(.monospaced)
                                    .foregroundStyle(.white)
                                    .padding(.horizontal, 8).padding(.vertical, 3)
                                    .background(BrandConfig.brand.opacity(0.8))
                                    .clipShape(Capsule())
                                Spacer()
                                Toggle("", isOn: Binding(
                                    get: { task.enabled },
                                    set: { newValue in
                                        Task {
                                            await service.toggleTask(
                                                agentId: agentId,
                                                taskId: task.id,
                                                enabled: newValue
                                            )
                                        }
                                    }
                                ))
                                .tint(BrandConfig.brand)
                                .labelsHidden()
                            }
                            Text(task.description)
                                .font(.subheadline)
                            Text(task.prompt)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineLimit(2)
                        }
                        .padding(.vertical, 4)
                    }
                    .onDelete { indexSet in
                        let toDelete = indexSet.map { service.tasks[$0] }
                        for task in toDelete {
                            Task {
                                await service.deleteTask(agentId: agentId, taskId: task.id)
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle(lang.t("スケジュールタスク", en: "Scheduled Tasks", zh: "定时任务", ko: "예약 작업"))
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    showAddTask = true
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .foregroundStyle(BrandConfig.brand)
                }
            }
        }
        .sheet(isPresented: $showAddTask) {
            AddTaskSheet(agentId: agentId, service: service) {
                showAddTask = false
            }
        }
        .task { await service.fetchTasks(agentId: agentId) }
        .refreshable { await service.fetchTasks(agentId: agentId) }
    }
}

// MARK: - Add Task Sheet

private struct AddTaskSheet: View {
    let agentId: String
    let service: AgentDetailService
    let onDismiss: () -> Void

    @State private var cronExpression = ""
    @State private var prompt = ""
    @State private var taskDescription = ""
    @State private var isSaving = false
    @Environment(\.lang) var lang
    @Environment(\.dismiss) var dismiss

    var isValid: Bool {
        !cronExpression.trimmingCharacters(in: .whitespaces).isEmpty &&
        !prompt.trimmingCharacters(in: .whitespaces).isEmpty &&
        !taskDescription.trimmingCharacters(in: .whitespaces).isEmpty
    }

    var body: some View {
        NavigationStack {
            Form {
                Section(header: Text(lang.t("Cron式", en: "Cron Expression", zh: "Cron 表达式", ko: "Cron 표현식"))) {
                    TextField("0 9 * * *", text: $cronExpression)
                        .fontDesign(.monospaced)
                }

                Section(header: Text(lang.t("説明", en: "Description", zh: "描述", ko: "설명"))) {
                    TextField(
                        lang.t("タスクの説明", en: "Task description", zh: "任务描述", ko: "작업 설명"),
                        text: $taskDescription
                    )
                }

                Section(header: Text(lang.t("プロンプト", en: "Prompt", zh: "提示词", ko: "프롬프트"))) {
                    TextEditor(text: $prompt)
                        .frame(minHeight: 100)
                }
            }
            .navigationTitle(lang.t("タスク追加", en: "Add Task", zh: "添加任务", ko: "작업 추가"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소")) { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button {
                        Task {
                            isSaving = true
                            await service.createTask(
                                agentId: agentId,
                                cron: cronExpression.trimmingCharacters(in: .whitespaces),
                                prompt: prompt.trimmingCharacters(in: .whitespaces),
                                description: taskDescription.trimmingCharacters(in: .whitespaces)
                            )
                            isSaving = false
                            onDismiss()
                        }
                    } label: {
                        if isSaving { ProgressView() }
                        else { Text(lang.t("保存", en: "Save", zh: "保存", ko: "저장")) }
                    }
                    .disabled(!isValid || isSaving)
                }
            }
        }
        .presentationDetents([.medium, .large])
    }
}
