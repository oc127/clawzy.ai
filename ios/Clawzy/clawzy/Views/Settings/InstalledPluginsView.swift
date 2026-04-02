import SwiftUI

// MARK: - InstalledPluginsView

struct InstalledPluginsView: View {
    let agent: Agent
    @Environment(PluginsStore.self) var pluginsStore
    @State private var uninstallingSlug: String?
    @State private var errorMessage: String?
    @Environment(\.lang) var lang

    private var plugins: [InstalledPlugin] { pluginsStore.plugins(for: agent.id) }
    private var isLoading: Bool { pluginsStore.isLoading(agentId: agent.id) }

    var body: some View {
        List {
            if isLoading && plugins.isEmpty {
                HStack {
                    Spacer()
                    ProgressView()
                    Spacer()
                }
                .listRowBackground(Color.clear)
            } else if plugins.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "puzzlepiece")
                        .font(.largeTitle)
                        .foregroundStyle(.secondary)
                    Text(lang.t("インストール済みプラグインなし",
                                en: "No installed plugins",
                                zh: "没有已安装的插件",
                                ko: "설치된 플러그인 없음"))
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 32)
                .listRowBackground(Color.clear)
            } else {
                ForEach(plugins) { plugin in
                    HStack {
                        VStack(alignment: .leading, spacing: 3) {
                            Text(plugin.name ?? plugin.slug)
                                .fontWeight(.medium)
                            HStack(spacing: 4) {
                                Text(plugin.slug)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                if let ver = plugin.version {
                                    Text("@\(ver)")
                                        .font(.caption)
                                        .foregroundStyle(.tertiary)
                                }
                            }
                        }
                        Spacer()
                        if uninstallingSlug == plugin.slug {
                            ProgressView()
                        } else {
                            Button(role: .destructive) {
                                Task { await uninstall(slug: plugin.slug) }
                            } label: {
                                Text(lang.t("削除", en: "Remove", zh: "卸载", ko: "제거"))
                                    .font(.subheadline)
                            }
                            .buttonStyle(.bordered)
                            .tint(.red)
                        }
                    }
                    .padding(.vertical, 2)
                }
            }
        }
        .navigationTitle(lang.t("インストール済みプラグイン",
                                en: "Installed Plugins",
                                zh: "已安装插件",
                                ko: "설치된 플러그인"))
        .navigationBarTitleDisplayMode(.inline)
        .refreshable { await pluginsStore.fetch(agentId: agent.id) }
        .task { await pluginsStore.fetch(agentId: agent.id) }
        .alert(lang.t("エラー", en: "Error", zh: "错误", ko: "오류"),
               isPresented: Binding(get: { errorMessage != nil },
                                    set: { if !$0 { errorMessage = nil } })) {
            Button(lang.t("OK", en: "OK", zh: "确定", ko: "확인")) { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
    }

    // MARK: - API

    private func uninstall(slug: String) async {
        uninstallingSlug = slug
        defer { uninstallingSlug = nil }
        do {
            try await pluginsStore.uninstall(slug: slug, agentId: agent.id)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
