import SwiftUI

struct MarketView: View {
    @State private var selectedTab = 0           // 0 = テンプレート, 1 = プラグイン
    @State private var selectedCategory = 0
    @State private var clawHubService = ClawHubService()
    @State private var searchText = ""
    @State private var searchTask: Task<Void, Never>?

    // Toast state
    @State private var toastMessage: String?
    @State private var toastIsError = false

    let categories = ["すべて", "ビジネス", "教育", "創作", "分析", "コード"]

    let templates: [AgentTemplate] = [
        AgentTemplate(icon: "💼", name: "ビジネスアシスタント", desc: "メール・資料作成・会議サポート", model: "deepseek-chat", tag: "人気"),
        AgentTemplate(icon: "📚", name: "日本語家庭教師", desc: "日本語学習をサポートします", model: "qwen-plus", tag: "教育"),
        AgentTemplate(icon: "✍️", name: "コピーライター", desc: "広告・SNS・ブログ文章を作成", model: "deepseek-chat", tag: "創作"),
        AgentTemplate(icon: "📊", name: "データアナリスト", desc: "データ分析・レポート作成", model: "deepseek-reasoner", tag: "分析"),
        AgentTemplate(icon: "💻", name: "コードレビュアー", desc: "コードレビュー・バグ修正サポート", model: "deepseek-chat", tag: "コード"),
        AgentTemplate(icon: "🎨", name: "クリエイティブライター", desc: "小説・詩・脚本の執筆サポート", model: "qwen-max", tag: "創作"),
        AgentTemplate(icon: "🌐", name: "翻訳スペシャリスト", desc: "日英中韓の高精度翻訳", model: "qwen-plus", tag: "ビジネス"),
        AgentTemplate(icon: "🔍", name: "リサーチアシスタント", desc: "調査・要約・情報整理", model: "deepseek-reasoner", tag: "分析"),
    ]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Tab switcher
                Picker("", selection: $selectedTab) {
                    Text("テンプレート").tag(0)
                    Text("プラグイン").tag(1)
                }
                .pickerStyle(.segmented)
                .padding(.horizontal, 16)
                .padding(.top, 8)
                .padding(.bottom, 4)

                if selectedTab == 0 {
                    templatesTab
                } else {
                    pluginsTab
                }
            }
            .background(BrandConfig.backgroundColor)
            .navigationTitle("マーケット")
            .overlay(alignment: .bottom) {
                if let msg = toastMessage {
                    ToastView(message: msg, isError: toastIsError)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                        .padding(.bottom, 24)
                }
            }
            .animation(.easeInOut(duration: 0.25), value: toastMessage)
        }
        .onChange(of: selectedTab) { _, newVal in
            if newVal == 1 && clawHubService.plugins.isEmpty {
                Task { await clawHubService.search() }
            }
        }
    }

    // MARK: - Templates tab

    private var templatesTab: some View {
        ScrollView {
            VStack(spacing: 0) {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(categories.indices, id: \.self) { i in
                            Button {
                                selectedCategory = i
                            } label: {
                                Text(categories[i])
                                    .font(.footnote)
                                    .fontWeight(.medium)
                                    .foregroundStyle(selectedCategory == i ? .white : .primary)
                                    .padding(.horizontal, 14)
                                    .padding(.vertical, 8)
                                    .background(
                                        selectedCategory == i
                                            ? BrandConfig.brand
                                            : BrandConfig.disabledGray
                                    )
                                    .clipShape(Capsule())
                            }
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                }

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                    ForEach(templates) { t in
                        TemplateCard(template: t)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 24)
            }
        }
    }

    // MARK: - Plugins tab

    private var pluginsTab: some View {
        VStack(spacing: 0) {
            // Search bar
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("プラグインを検索...", text: $searchText)
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)
                    .onSubmit { triggerSearch() }
                if !searchText.isEmpty {
                    Button {
                        searchText = ""
                        triggerSearch()
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(BrandConfig.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .onChange(of: searchText) { _, _ in triggerSearch() }

            // Results
            if clawHubService.isLoading && clawHubService.plugins.isEmpty {
                Spacer()
                ProgressView()
                Spacer()
            } else if let err = clawHubService.errorMessage, clawHubService.plugins.isEmpty {
                emptyState(
                    icon: "wifi.slash",
                    title: "接続エラー",
                    subtitle: err
                )
            } else if clawHubService.plugins.isEmpty {
                emptyState(
                    icon: "tray",
                    title: "プラグインが見つかりません",
                    subtitle: "別のキーワードで検索してみてください"
                )
            } else {
                ScrollView {
                    LazyVStack(spacing: 10) {
                        ForEach(clawHubService.plugins) { plugin in
                            PluginCard(plugin: plugin) { agentId in
                                await installPlugin(plugin: plugin, agentId: agentId)
                            }
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.bottom, 24)
                }
            }
        }
    }

    // MARK: - Helpers

    private func triggerSearch() {
        searchTask?.cancel()
        searchTask = Task {
            try? await Task.sleep(for: .milliseconds(350))
            guard !Task.isCancelled else { return }
            await clawHubService.search(query: searchText)
        }
    }

    private func installPlugin(plugin: ClawHubPlugin, agentId: String) async {
        do {
            try await clawHubService.install(agentId: agentId, slug: plugin.slug)
            showToast("\(plugin.name) をインストールしました", isError: false)
        } catch {
            showToast("インストール失敗: \(error.localizedDescription)", isError: true)
        }
    }

    private func showToast(_ message: String, isError: Bool) {
        toastMessage = message
        toastIsError = isError
        Task {
            try? await Task.sleep(for: .seconds(3))
            toastMessage = nil
        }
    }

    @ViewBuilder
    private func emptyState(icon: String, title: String, subtitle: String) -> some View {
        VStack(spacing: 12) {
            Spacer()
            Image(systemName: icon)
                .font(.system(size: 40))
                .foregroundStyle(.secondary)
            Text(title)
                .font(.headline)
            Text(subtitle)
                .font(.footnote)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            Spacer()
        }
    }
}

// MARK: - Plugin card

private struct PluginCard: View {
    let plugin: ClawHubPlugin
    let onInstall: (String) async -> Void

    @State private var showAgentPicker = false
    @State private var isInstalling = false
    @State private var installed = false
    @State private var agentService = AgentService()

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 3) {
                    Text(plugin.name)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                    if let author = plugin.author {
                        Text(author)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                Spacer()
                installButton
            }

            if let desc = plugin.description, !desc.isEmpty {
                Text(desc)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }

            HStack(spacing: 10) {
                if let version = plugin.version {
                    Label(version, systemImage: "tag")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                if let dl = plugin.downloads {
                    Label(formatDownloads(dl), systemImage: "arrow.down.circle")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                if let tags = plugin.tags, let first = tags.first {
                    Text(first)
                        .font(.caption2)
                        .fontWeight(.medium)
                        .foregroundStyle(BrandConfig.brand)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(BrandConfig.brand.opacity(0.10))
                        .clipShape(Capsule())
                }
                Spacer()
            }
        }
        .padding(14)
        .background(BrandConfig.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.04), radius: 4, y: 2)
        .sheet(isPresented: $showAgentPicker) {
            AgentPickerSheet(agentService: agentService) { agentId in
                showAgentPicker = false
                isInstalling = true
                Task {
                    await onInstall(agentId)
                    isInstalling = false
                    installed = true
                }
            }
        }
        .task {
            if agentService.agents.isEmpty { await agentService.fetchAgents() }
        }
    }

    @ViewBuilder
    private var installButton: some View {
        Button {
            if !installed && !isInstalling {
                showAgentPicker = true
            }
        } label: {
            Group {
                if isInstalling {
                    ProgressView()
                        .controlSize(.small)
                        .tint(BrandConfig.brand)
                } else {
                    HStack(spacing: 4) {
                        Image(systemName: installed ? "checkmark" : "arrow.down.circle")
                            .font(.caption.bold())
                        Text(installed ? "済み" : "インストール")
                            .font(.caption)
                            .fontWeight(.medium)
                    }
                    .foregroundStyle(installed ? .secondary : BrandConfig.brand)
                }
            }
            .frame(minWidth: 80)
            .padding(.vertical, 6)
            .padding(.horizontal, 10)
            .background(
                installed
                    ? BrandConfig.disabledGray
                    : BrandConfig.brand.opacity(0.09)
            )
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .disabled(installed || isInstalling)
    }

    private func formatDownloads(_ n: Int) -> String {
        if n >= 1000 { return "\(n / 1000)k" }
        return "\(n)"
    }
}

// MARK: - Agent picker sheet

private struct AgentPickerSheet: View {
    let agentService: AgentService
    let onSelect: (String) -> Void

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Group {
                if agentService.agents.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "person.crop.circle.badge.questionmark")
                            .font(.system(size: 40))
                            .foregroundStyle(.secondary)
                        Text("エージェントがありません")
                            .font(.headline)
                        Text("まずダッシュボードでエージェントを作成してください")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 32)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(agentService.agents) { agent in
                        Button {
                            onSelect(agent.id)
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(agent.name)
                                        .font(.subheadline)
                                        .fontWeight(.medium)
                                        .foregroundStyle(.primary)
                                    Text(agent.modelName)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .navigationTitle("インストール先を選択")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("キャンセル") { dismiss() }
                }
            }
        }
        .presentationDetents([.medium])
    }
}

// MARK: - Toast

private struct ToastView: View {
    let message: String
    let isError: Bool

    var body: some View {
        Text(message)
            .font(.footnote)
            .fontWeight(.medium)
            .foregroundStyle(.white)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(isError ? Color.red.opacity(0.9) : Color.green.opacity(0.85))
            .clipShape(Capsule())
            .shadow(color: .black.opacity(0.15), radius: 8, y: 4)
    }
}

// MARK: - Template card

private struct TemplateCard: View {
    let template: AgentTemplate
    @State private var added = false
    @Environment(AuthManager.self) var authManager

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(template.icon)
                    .font(.largeTitle)
                Spacer()
                Text(template.tag)
                    .font(.caption2)
                    .fontWeight(.semibold)
                    .foregroundStyle(BrandConfig.brand)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 3)
                    .background(BrandConfig.brand.opacity(0.10))
                    .clipShape(Capsule())
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(template.name)
                    .font(.footnote)
                    .fontWeight(.semibold)
                    .lineLimit(1)
                Text(template.desc)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }

            Spacer()

            Button {
                withAnimation(.spring(duration: 0.3)) { added = true }
                Task {
                    let service = AgentService()
                    _ = await service.createAgent(name: template.name, modelName: template.model)
                }
            } label: {
                HStack(spacing: 4) {
                    Image(systemName: added ? "checkmark" : "plus")
                        .font(.caption.bold())
                    Text(added ? "追加済み" : "追加する")
                        .font(.caption)
                        .fontWeight(.medium)
                }
                .foregroundStyle(added ? .secondary : BrandConfig.brand)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .background(added ? BrandConfig.disabledGray : BrandConfig.brand.opacity(0.09))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .disabled(added)
        }
        .padding(14)
        .frame(height: 180)
        .background(BrandConfig.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .shadow(color: .black.opacity(0.04), radius: 6, y: 2)
    }
}

// MARK: - Model

struct AgentTemplate: Identifiable {
    let id = UUID()
    let icon: String
    let name: String
    let desc: String
    let model: String
    let tag: String
}
