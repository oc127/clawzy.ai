import SwiftUI

struct CreateAgentView: View {
    @Bindable var agentService: AgentService
    @Environment(\.dismiss) var dismiss

    @State private var name = ""
    @State private var selectedModel = "deepseek-chat"
    @State private var isCreating = false
    @State private var showError = false

    let availableModels: [(id: String, name: String, desc: String, badge: String)] = [
        ("deepseek-chat",     "DeepSeek V3",  "高コスパ汎用モデル",   "おすすめ"),
        ("deepseek-reasoner", "DeepSeek R1",  "強い推論能力",         "推論"),
        ("qwen-turbo",        "Qwen Turbo",   "最速レスポンス",        "高速"),
        ("qwen-plus",         "Qwen Plus",    "バランス型",            ""),
        ("qwen-max",          "Qwen Max",     "通義最強モデル",         "最強"),
    ]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Name field
                    VStack(alignment: .leading, spacing: 12) {
                        Text("エージェント名")
                            .font(.footnote)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)
                            .textCase(.uppercase)

                        LabeledField(label: "名前") {
                            TextField("例: 日本語アシスタント", text: $name)
                                .textFieldStyle(.plain)
                                .autocorrectionDisabled()
                        }
                    }

                    // Model selection
                    VStack(alignment: .leading, spacing: 12) {
                        Text("モデルを選択")
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

                    BrandButton(title: isCreating ? "" : "作成する", isLoading: isCreating) {
                        Task {
                            isCreating = true
                            let agent = await agentService.createAgent(name: name, modelName: selectedModel)
                            isCreating = false
                            if agent != nil {
                                dismiss()
                            } else {
                                showError = true
                            }
                        }
                    }
                    .disabled(name.isEmpty || isCreating)
                    .padding(.top, 8)
                }
                .padding(20)
            }
            .background(BrandConfig.backgroundColor)
            .navigationTitle("エージェントを作成")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("キャンセル") { dismiss() }
                        .foregroundStyle(BrandConfig.brand)
                }
            }
            .alert("作成に失敗しました", isPresented: $showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(agentService.errorMessage ?? "不明なエラーが発生しました")
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
                        .foregroundStyle(isSelected ? BrandConfig.brand : Color(white: 0.55))
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
