import SwiftUI

struct PipelineDetailView: View {
    let pipeline: TaskPipeline
    let service: PipelineService
    @State private var detail: TaskPipeline?
    @State private var isRunning = false
    @Environment(\.lang) var lang

    private var current: TaskPipeline { detail ?? pipeline }

    private var statusColor: Color {
        switch current.status {
        case .completed:  return Color(UIColor.systemGreen)
        case .running:    return Color(UIColor.systemBlue)
        case .failed:     return BrandConfig.brand
        case .ready:      return Color(UIColor.systemOrange)
        default:          return Color(UIColor.systemGray)
        }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: BrandConfig.Spacing.lg) {
                statusCard
                if let steps = current.steps, !steps.isEmpty {
                    stepsSection(steps)
                }
                if let summary = current.resultSummary {
                    summarySection(summary)
                }
            }
            .padding(BrandConfig.Spacing.lg)
            .padding(.bottom, BrandConfig.Spacing.xl)
        }
        .background(BrandConfig.darkBg)
        .navigationTitle(current.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if current.status == .ready || current.status == .planning {
                ToolbarItem(placement: .primaryAction) {
                    Button { Task { await runPipeline() } } label: {
                        if isRunning {
                            ProgressView().scaleEffect(0.8)
                        } else {
                            Label(lang.t("実行", en: "Run", zh: "运行", ko: "실행"),
                                  systemImage: "play.fill")
                                .fontWeight(.semibold)
                        }
                    }
                    .disabled(isRunning)
                }
            }
        }
        .task { await loadDetail() }
    }

    // MARK: - Status card

    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(lang.current == "en" ? current.status.labelEn : current.status.label)
                    .font(.caption).fontWeight(.semibold)
                    .foregroundStyle(statusColor)
                    .padding(.horizontal, 10).padding(.vertical, 4)
                    .background(statusColor.opacity(0.12))
                    .clipShape(Capsule())
                Spacer()
                if current.totalSteps > 0 {
                    Text("\(current.completedSteps)/\(current.totalSteps) "
                         + lang.t("ステップ", en: "steps", zh: "步", ko: "단계"))
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            if current.totalSteps > 0 {
                ProgressView(value: Double(current.completedSteps), total: Double(current.totalSteps))
                    .tint(statusColor)
            }
            if let prompt = current.originalPrompt {
                Text(prompt)
                    .font(.subheadline).foregroundStyle(.secondary)
                    .lineLimit(4)
            }
        }
        .padding(BrandConfig.Spacing.lg)
        .background(BrandConfig.darkCard)
        .clipShape(RoundedRectangle(cornerRadius: BrandConfig.Radius.card))
        .overlay(RoundedRectangle(cornerRadius: BrandConfig.Radius.card)
            .stroke(BrandConfig.darkSeparator, lineWidth: 1))
    }

    // MARK: - Steps

    private func stepsSection(_ steps: [PipelineStep]) -> some View {
        VStack(alignment: .leading, spacing: BrandConfig.Spacing.sm) {
            Text(lang.t("実行ステップ", en: "Steps", zh: "执行步骤", ko: "실행 단계"))
                .font(.headline).fontWeight(.bold)
            VStack(spacing: BrandConfig.Spacing.sm) {
                ForEach(steps) { step in
                    StepCard(step: step)
                }
            }
        }
    }

    // MARK: - Result summary

    private func summarySection(_ summary: String) -> some View {
        VStack(alignment: .leading, spacing: BrandConfig.Spacing.sm) {
            Text(lang.t("結果サマリー", en: "Result Summary", zh: "结果摘要", ko: "결과 요약"))
                .font(.headline).fontWeight(.bold)
            Text(summary)
                .font(.subheadline).foregroundStyle(.secondary)
                .padding(BrandConfig.Spacing.lg)
                .background(BrandConfig.darkCard)
                .clipShape(RoundedRectangle(cornerRadius: BrandConfig.Radius.card))
                .overlay(RoundedRectangle(cornerRadius: BrandConfig.Radius.card)
                    .stroke(BrandConfig.darkSeparator, lineWidth: 1))
        }
    }

    // MARK: - Actions

    private func loadDetail() async {
        detail = await service.fetchDetail(pipeline.id)
    }

    private func runPipeline() async {
        isRunning = true
        defer { isRunning = false }
        if let updated = await service.runPipeline(pipeline.id) {
            detail = updated
        }
    }
}

// MARK: - Step Card

private struct StepCard: View {
    let step: PipelineStep

    private var statusColor: Color {
        switch step.status {
        case .completed: return Color(UIColor.systemGreen)
        case .running:   return Color(UIColor.systemBlue)
        case .failed:    return .red
        case .skipped:   return Color(UIColor.systemGray)
        default:         return Color(UIColor.systemGray3)
        }
    }

    private var roleEmoji: String {
        switch step.agentRole {
        case "researcher": return "🔍"
        case "coder":      return "💻"
        case "writer":     return "✍️"
        case "analyst":    return "📊"
        case "reviewer":   return "✅"
        default:           return "🤖"
        }
    }

    var body: some View {
        HStack(alignment: .top, spacing: BrandConfig.Spacing.md) {
            stepIndicator
            VStack(alignment: .leading, spacing: 4) {
                HStack(alignment: .firstTextBaseline) {
                    Text("\(roleEmoji) \(step.title)")
                        .font(.callout).fontWeight(.medium)
                        .foregroundStyle(.primary)
                    Spacer()
                    if let score = step.evaluationScore {
                        Text(String(format: "%.0f/10", score))
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                }
                if let desc = step.description {
                    Text(desc)
                        .font(.caption).foregroundStyle(.secondary)
                        .lineLimit(2)
                }
                Text(step.agentRole)
                    .font(.caption2).foregroundStyle(.secondary)
                    .padding(.horizontal, 6).padding(.vertical, 2)
                    .background(Color(UIColor.tertiarySystemFill))
                    .clipShape(Capsule())
            }
        }
        .padding(BrandConfig.Spacing.md)
        .background(BrandConfig.darkCard)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12)
            .stroke(BrandConfig.darkSeparator, lineWidth: 1))
    }

    private var stepIndicator: some View {
        ZStack {
            Circle()
                .fill(statusColor.opacity(0.15))
                .frame(width: 36, height: 36)
            Group {
                switch step.status {
                case .running:
                    ProgressView().scaleEffect(0.7)
                case .completed:
                    Image(systemName: "checkmark")
                        .font(.caption).fontWeight(.bold)
                        .foregroundStyle(statusColor)
                case .failed:
                    Image(systemName: "xmark")
                        .font(.caption).fontWeight(.bold)
                        .foregroundStyle(statusColor)
                case .skipped:
                    Image(systemName: "forward.fill")
                        .font(.caption)
                        .foregroundStyle(statusColor)
                default:
                    Text("\(step.stepOrder)")
                        .font(.caption).fontWeight(.semibold)
                        .foregroundStyle(statusColor)
                }
            }
        }
    }
}
