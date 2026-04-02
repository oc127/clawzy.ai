import SwiftUI

struct ToolsView: View {
    let agentId: String
    @State private var service = AgentDetailService()
    @Environment(\.lang) var lang

    var body: some View {
        Group {
            if service.isLoading && service.tools.isEmpty {
                ProgressView(lang.t("読み込み中...", en: "Loading...", zh: "加载中...", ko: "로딩 중..."))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if service.tools.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "wrench.and.screwdriver")
                        .font(.largeTitle)
                        .foregroundStyle(.secondary)
                    Text(lang.t("ツールがありません", en: "No tools available", zh: "暂无工具", ko: "사용 가능한 도구가 없습니다"))
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List {
                    ForEach(service.tools) { tool in
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(tool.name)
                                    .font(.subheadline).fontWeight(.medium)
                                Text(tool.description)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(2)
                            }
                            Spacer()
                            Toggle("", isOn: Binding(
                                get: { tool.enabled },
                                set: { newValue in
                                    Task {
                                        await service.toggleTool(
                                            agentId: agentId,
                                            toolName: tool.name,
                                            enabled: newValue
                                        )
                                    }
                                }
                            ))
                            .tint(BrandConfig.brand)
                            .labelsHidden()
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
        }
        .navigationTitle(lang.t("ツール", en: "Tools", zh: "工具", ko: "도구"))
        .navigationBarTitleDisplayMode(.inline)
        .task { await service.fetchTools(agentId: agentId) }
        .refreshable { await service.fetchTools(agentId: agentId) }
    }
}
