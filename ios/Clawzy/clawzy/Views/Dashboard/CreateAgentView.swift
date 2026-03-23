import SwiftUI

struct CreateAgentView: View {
    @Bindable var agentService: AgentService
    @Environment(\.dismiss) var dismiss

    @State private var name = ""
    @State private var selectedModel = "deepseek-chat"
    @State private var isCreating = false

    // 可选模型列表（和后端 LiteLLM 配置对应）
    let availableModels = [
        ("deepseek-chat", "DeepSeek V3", "高性价比通用模型"),
        ("deepseek-reasoner", "DeepSeek R1", "强推理能力"),
        ("qwen-turbo", "Qwen Turbo", "速度最快"),
        ("qwen-plus", "Qwen Plus", "平衡之选"),
        ("qwen-max", "Qwen Max", "通义最强"),
    ]

    var body: some View {
        NavigationStack {
            Form {
                Section("Agent 名称") {
                    TextField("给你的龙虾起个名字", text: $name)
                }

                Section("选择模型") {
                    ForEach(availableModels, id: \.0) { model in
                        Button {
                            selectedModel = model.0
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(model.1)
                                        .foregroundStyle(.primary)
                                        .fontWeight(.medium)
                                    Text(model.2)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                if selectedModel == model.0 {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundStyle(.orange)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("创建 Agent")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button {
                        Task {
                            isCreating = true
                            let _ = await agentService.createAgent(
                                name: name,
                                modelName: selectedModel
                            )
                            isCreating = false
                            dismiss()
                        }
                    } label: {
                        if isCreating {
                            ProgressView()
                        } else {
                            Text("创建")
                        }
                    }
                    .disabled(name.isEmpty || isCreating)
                }
            }
        }
    }
}
