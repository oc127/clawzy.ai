import SwiftUI

struct HarnessView: View {
    @Environment(\.lang) var lang
    @State private var service = PipelineService()
    @State private var showCreate = false
    @State private var newPrompt = ""
    @State private var isCreating = false

    var body: some View {
        Group {
            if service.isLoading && service.pipelines.isEmpty {
                ProgressView(lang.t("読み込み中...", en: "Loading...", zh: "加载中...", ko: "로딩 중..."))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(BrandConfig.darkBg)
            } else if service.pipelines.isEmpty {
                emptyState
            } else {
                pipelineList
            }
        }
        .navigationTitle(lang.t("パイプライン", en: "Pipelines", zh: "流水线", ko: "파이프라인"))
        .navigationBarTitleDisplayMode(.large)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button { showCreate = true } label: {
                    Image(systemName: "plus")
                        .fontWeight(.semibold)
                }
            }
        }
        .sheet(isPresented: $showCreate) { createSheet }
        .task { await service.fetchPipelines() }
        .refreshable { await service.fetchPipelines() }
        .background(BrandConfig.darkBg)
    }

    // MARK: - Pipeline list

    private var pipelineList: some View {
        ScrollView {
            VStack(spacing: BrandConfig.Spacing.md) {
                ForEach(service.pipelines) { pipeline in
                    NavigationLink {
                        PipelineDetailView(pipeline: pipeline, service: service)
                    } label: {
                        PipelineRow(pipeline: pipeline)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, BrandConfig.Spacing.lg)
            .padding(.top, BrandConfig.Spacing.md)
            .padding(.bottom, BrandConfig.Spacing.xl)
        }
        .background(BrandConfig.darkBg)
    }

    // MARK: - Empty state

    private var emptyState: some View {
        VStack(spacing: BrandConfig.Spacing.lg) {
            Text("🔗").font(.system(size: 56))
            VStack(spacing: 6) {
                Text(lang.t("パイプラインがありません",
                            en: "No pipelines yet",
                            zh: "还没有流水线",
                            ko: "파이프라인 없음"))
                    .font(.headline).fontWeight(.semibold)
                Text(lang.t("複雑なタスクを複数のAgentで実行できます",
                            en: "Run complex tasks with multiple AI agents",
                            zh: "用多个Agent协作完成复杂任务",
                            ko: "여러 에이전트로 복잡한 작업 실행"))
                    .font(.subheadline).foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            Button { showCreate = true } label: {
                Label(lang.t("パイプラインを作成", en: "Create Pipeline", zh: "创建流水线", ko: "파이프라인 만들기"),
                      systemImage: "plus")
                    .font(.callout).fontWeight(.semibold)
                    .padding(.horizontal, 24).padding(.vertical, 12)
                    .background(BrandConfig.brand)
                    .foregroundStyle(.white)
                    .clipShape(Capsule())
            }
        }
        .padding(BrandConfig.Spacing.xl)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(BrandConfig.darkBg)
    }

    // MARK: - Create sheet

    private var createSheet: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: BrandConfig.Spacing.lg) {
                Text(lang.t("実行したいタスクを説明してください。AIが自動的にサブタスクに分解して実行します。",
                            en: "Describe the task you want to execute. AI will automatically break it into subtasks.",
                            zh: "请描述您想执行的任务。AI将自动分解成子任务并逐步执行。",
                            ko: "실행할 작업을 설명하세요. AI가 자동으로 서브태스크로 분해하여 실행합니다."))
                    .font(.subheadline).foregroundStyle(.secondary)

                TextEditor(text: $newPrompt)
                    .frame(minHeight: 160)
                    .padding(12)
                    .background(BrandConfig.darkCard)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(BrandConfig.darkSeparator, lineWidth: 1)
                    )

                Spacer()
            }
            .padding(BrandConfig.Spacing.lg)
            .background(BrandConfig.darkBg)
            .navigationTitle(lang.t("新規パイプライン", en: "New Pipeline", zh: "新建流水线", ko: "새 파이프라인"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소")) {
                        showCreate = false
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(lang.t("作成", en: "Create", zh: "创建", ko: "만들기")) {
                        Task { await submitCreate() }
                    }
                    .disabled(newPrompt.trimmingCharacters(in: .whitespaces).isEmpty || isCreating)
                    .fontWeight(.semibold)
                }
            }
        }
        .presentationDetents([.medium, .large])
    }

    private func submitCreate() async {
        isCreating = true
        defer { isCreating = false }
        let trimmed = newPrompt.trimmingCharacters(in: .whitespaces)
        if await service.createPipeline(prompt: trimmed) != nil {
            newPrompt = ""
            showCreate = false
        }
    }
}

// MARK: - Pipeline Row

private struct PipelineRow: View {
    let pipeline: TaskPipeline
    @Environment(\.lang) var lang

    private var statusColor: Color {
        switch pipeline.status {
        case .completed:  return Color(UIColor.systemGreen)
        case .running:    return Color(UIColor.systemBlue)
        case .failed:     return BrandConfig.brand
        case .ready:      return Color(UIColor.systemOrange)
        default:          return Color(UIColor.systemGray)
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(pipeline.title)
                        .font(.callout).fontWeight(.semibold)
                        .foregroundStyle(.primary)
                        .lineLimit(2)
                    if let prompt = pipeline.originalPrompt {
                        Text(prompt)
                            .font(.caption).foregroundStyle(.secondary)
                            .lineLimit(2)
                    }
                }
                Spacer()
                Text(lang.current == "en" ? pipeline.status.labelEn : pipeline.status.label)
                    .font(.caption2).fontWeight(.semibold)
                    .foregroundStyle(statusColor)
                    .padding(.horizontal, 8).padding(.vertical, 3)
                    .background(statusColor.opacity(0.12))
                    .clipShape(Capsule())
            }

            if pipeline.totalSteps > 0 {
                VStack(alignment: .leading, spacing: 4) {
                    ProgressView(value: Double(pipeline.completedSteps), total: Double(pipeline.totalSteps))
                        .tint(statusColor)
                    Text("\(pipeline.completedSteps)/\(pipeline.totalSteps) "
                         + lang.t("ステップ", en: "steps", zh: "步", ko: "단계"))
                        .font(.caption2).foregroundStyle(.secondary)
                }
            }
        }
        .padding(BrandConfig.Spacing.lg)
        .background(BrandConfig.darkCard)
        .clipShape(RoundedRectangle(cornerRadius: BrandConfig.Radius.card))
        .overlay(
            RoundedRectangle(cornerRadius: BrandConfig.Radius.card)
                .stroke(BrandConfig.darkSeparator, lineWidth: 1)
        )
    }
}
