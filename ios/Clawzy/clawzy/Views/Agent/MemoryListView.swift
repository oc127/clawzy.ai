import SwiftUI

struct MemoryListView: View {
    let agentId: String
    @State private var service = AgentDetailService()
    @Environment(\.lang) var lang

    var body: some View {
        Group {
            if service.isLoading && service.memories.isEmpty {
                ProgressView(lang.t("読み込み中...", en: "Loading...", zh: "加载中...", ko: "로딩 중..."))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if service.memories.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "brain.head.profile")
                        .font(.largeTitle)
                        .foregroundStyle(.secondary)
                    Text(lang.t("メモリがありません", en: "No memories yet", zh: "暂无记忆", ko: "메모리가 없습니다"))
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List {
                    ForEach(service.memories) { memory in
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(memory.type)
                                    .font(.caption2).fontWeight(.bold)
                                    .foregroundStyle(.white)
                                    .padding(.horizontal, 8).padding(.vertical, 3)
                                    .background(BrandConfig.brand)
                                    .clipShape(Capsule())
                                Spacer()
                                Text(formatDate(memory.createdAt))
                                    .font(.caption2)
                                    .foregroundStyle(.tertiary)
                            }
                            Text(memory.content)
                                .font(.subheadline)
                                .foregroundStyle(.primary)
                                .lineLimit(4)
                        }
                        .padding(.vertical, 4)
                    }
                    .onDelete { indexSet in
                        let toDelete = indexSet.map { service.memories[$0] }
                        for memory in toDelete {
                            Task {
                                await service.deleteMemory(agentId: agentId, memoryId: memory.id)
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle(lang.t("メモリ", en: "Memory", zh: "记忆", ko: "메모리"))
        .navigationBarTitleDisplayMode(.inline)
        .task { await service.fetchMemories(agentId: agentId) }
        .refreshable { await service.fetchMemories(agentId: agentId) }
    }

    private func formatDate(_ iso: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard let date = formatter.date(from: iso) else {
            formatter.formatOptions = [.withInternetDateTime]
            guard let date = formatter.date(from: iso) else { return iso }
            return date.formatted(.relative(presentation: .named))
        }
        return date.formatted(.relative(presentation: .named))
    }
}
