import SwiftUI

struct CreateAgentView: View {
    @Bindable var agentService: AgentService
    @Environment(\.dismiss) var dismiss
    @Environment(\.lang) var lang

    @State private var name = ""
    @State private var selectedModel = "deepseek-chat"
    @State private var isCreating = false

    var availableModels: [(id: String, name: String, desc: String, badge: String)] {
        [
            ("deepseek-chat",     "DeepSeek V3",  lang.t("高コスパ汎用モデル", en: "Cost-effective model", zh: "高性价比通用模型", ko: "가성비 범용 모델"),   lang.t("おすすめ", en: "Recommended", zh: "推荐", ko: "추천")),
            ("deepseek-reasoner", "DeepSeek R1",  lang.t("強い推論能力", en: "Strong reasoning", zh: "强推理能力", ko: "강력한 추론 능력"),         lang.t("推論", en: "Reasoning", zh: "推理", ko: "추론")),
            ("qwen-turbo",        "Qwen Turbo",   lang.t("最速レスポンス", en: "Fastest response", zh: "最快响应", ko: "최고속 응답"),        lang.t("高速", en: "Fast", zh: "快速", ko: "고속")),
            ("qwen-plus",         "Qwen Plus",    lang.t("バランス型", en: "Balanced", zh: "均衡型", ko: "밸런스형"),            ""),
            ("qwen-max",          "Qwen Max",     lang.t("通義最強モデル", en: "Most powerful", zh: "通义最强模型", ko: "최강 모델"),         lang.t("最強", en: "Strongest", zh: "最强", ko: "최강")),
        ]
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Name field
                    VStack(alignment: .leading, spacing: 12) {
                        Text(lang.t("エージェント名", en: "Agent Name", zh: "助手名称", ko: "에이전트 이름"))
                            .font(.footnote)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)
                            .textCase(.uppercase)

                        LabeledField(label: lang.t("名前", en: "Name", zh: "名称", ko: "이름")) {
                            TextField(lang.t("例: 日本語アシスタント", en: "e.g., My Assistant", zh: "例如：我的助手", ko: "예: 내 어시스턴트"), text: $name)
                                .textFieldStyle(.plain)
                                .autocorrectionDisabled()
                        }
                    }

                    // Model selection
                    VStack(alignment: .leading, spacing: 12) {
                        Text(lang.t("モデルを選択", en: "Select Model", zh: "选择模型", ko: "모델 선택"))
                            .font(.footnote)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)
                            .textCase(.uppercase)

                        VStack(spacing: 1) {
                            ForEach(availableModels, id: \.id) { model in
                                ModelRow(
                                    model: model,
                                    isSelected: selectedModel == model.id
                                ) {
                                    selectedModel = model.id
                                }
                            }
                        }
                        .background(BrandConfig.cardBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                    }

                    BrandButton(title: isCreating ? "" : lang.t("作成する", en: "Create", zh: "创建", ko: "만들기"), isLoading: isCreating) {
                        Task {
                            isCreating = true
                            let _ = await agentService.createAgent(name: name, modelName: selectedModel)
                            isCreating = false
                            dismiss()
                        }
                    }
                    .disabled(name.isEmpty || isCreating)
                    .padding(.top, 8)
                }
                .padding(20)
            }
            .background(BrandConfig.backgroundColor)
            .navigationTitle(lang.t("エージェントを作成", en: "Create Agent", zh: "创建助手", ko: "에이전트 만들기"))
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소")) { dismiss() }
                        .foregroundStyle(BrandConfig.brand)
                }
            }
        }
    }
}

private struct ModelRow: View {
    let model: (id: String, name: String, desc: String, badge: String)
    let isSelected: Bool
    let onSelect: () -> Void

    var body: some View {
        Button(action: onSelect) {
            HStack(spacing: 14) {
                ZStack {
                    Circle()
                        .fill(isSelected ? BrandConfig.brand.opacity(0.12) : BrandConfig.disabledGray)
                        .frame(width: 36, height: 36)
                    Image(systemName: "cpu")
                        .font(.footnote)
                        .foregroundStyle(isSelected ? BrandConfig.brand : .secondary)
                }

                VStack(alignment: .leading, spacing: 3) {
                    HStack(spacing: 6) {
                        Text(model.name)
                            .fontWeight(.medium)
                            .foregroundStyle(.primary)
                        if !model.badge.isEmpty {
                            Text(model.badge)
                                .font(.caption2)
                                .fontWeight(.semibold)
                                .foregroundStyle(BrandConfig.brand)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(BrandConfig.brand.opacity(0.10))
                                .clipShape(Capsule())
                        }
                    }
                    Text(model.desc)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(BrandConfig.brand)
                        .font(.title3)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(BrandConfig.cardBackground)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}
