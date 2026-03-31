import SwiftUI

// MARK: - Plugin model

struct InstalledPlugin: Identifiable, Decodable {
    var id: String { slug }
    let slug: String
    let version: String?
    let name: String?
}

private struct PluginsResponse: Decodable {
    let plugins: [InstalledPlugin]
}

// MARK: - InstalledPluginsView

struct InstalledPluginsView: View {
    let agent: Agent
    @State private var plugins: [InstalledPlugin] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var uninstallingSlug: String?
    @Environment(\.lang) var lang

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
        .refreshable { await fetchPlugins() }
        .task { await fetchPlugins() }
        .alert(lang.t("エラー", en: "Error", zh: "错误", ko: "오류"),
               isPresented: Binding(get: { errorMessage != nil },
                                    set: { if !$0 { errorMessage = nil } })) {
            Button("OK") { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
    }

    // MARK: - API

    private func fetchPlugins() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let resp: PluginsResponse = try await APIClient.shared.request(
                Constants.API.agentPlugins(agent.id)
            )
            await MainActor.run { plugins = resp.plugins }
        } catch {
            await MainActor.run { errorMessage = error.localizedDescription }
        }
    }

    private func uninstall(slug: String) async {
        await MainActor.run { uninstallingSlug = slug }
        defer { Task { @MainActor in uninstallingSlug = nil } }
        do {
            try await APIClient.shared.requestVoid(
                Constants.API.agentPlugin(agent.id, slug: slug),
                method: "DELETE"
            )
            await MainActor.run { plugins.removeAll { $0.slug == slug } }
        } catch {
            await MainActor.run { errorMessage = error.localizedDescription }
        }
    }
}
