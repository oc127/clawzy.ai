import SwiftUI

struct MarketView: View {
    @Environment(AgentService.self) var agentService
    @Environment(PluginsStore.self) var pluginsStore
    @Environment(\.lang) var lang

    @State private var selectedTab = 0
    @State private var clawHubService = ClawHubService()
    @State private var popularService = ClawHubService()
    @State private var searchText = ""
    @State private var searchTask: Task<Void, Never>?

    // Install confirmation modal
    @State private var selectedPlugin: ClawHubPlugin?
    @State private var isConfirmInstalling = false

    // Toast state
    @State private var toastMessage: String?
    @State private var toastIsError = false

    var body: some View {
        ZStack {
            NavigationStack {
                VStack(spacing: 0) {
                    Picker("", selection: $selectedTab) {
                        Text(lang.t("テンプレート", en: "Templates", zh: "模板", ko: "템플릿")).tag(0)
                        Text(lang.t("プラグイン",   en: "Plugins",   zh: "插件", ko: "플러그인")).tag(1)
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
                .navigationTitle(lang.t("マーケット", en: "Market", zh: "市场", ko: "마켓"))
                .overlay(alignment: .bottom) {
                    if let msg = toastMessage {
                        ToastView(message: msg, isError: toastIsError)
                            .transition(.move(edge: .bottom).combined(with: .opacity))
                            .padding(.bottom, 24)
                    }
                }
                .animation(.easeInOut(duration: 0.25), value: toastMessage)
            }

            // MARK: - Centered install confirmation overlay
            if selectedPlugin != nil {
                Color.black.opacity(0.5)
                    .ignoresSafeArea()
                    .onTapGesture {
                        if !isConfirmInstalling { selectedPlugin = nil }
                    }
                    .transition(.opacity)

                if let plugin = selectedPlugin {
                    installConfirmCard(plugin: plugin)
                        .transition(.scale(scale: 0.92).combined(with: .opacity))
                }
            }
        }
        .animation(.spring(response: 0.28, dampingFraction: 0.82), value: selectedPlugin != nil)
        .onChange(of: selectedTab) { _, newVal in
            if newVal == 1 && clawHubService.plugins.isEmpty {
                Task { await clawHubService.search() }
            }
        }
    }

    // MARK: - Install confirmation card

    @ViewBuilder
    private func installConfirmCard(plugin: ClawHubPlugin) -> some View {
        VStack(spacing: 0) {
            // Close button row
            HStack {
                Spacer()
                Button {
                    if !isConfirmInstalling { selectedPlugin = nil }
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title2)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.bottom, 8)

            // Icon
            Text(iconForPlugin(plugin))
                .font(.system(size: 52))
                .padding(.bottom, 12)

            // Name
            Text(plugin.name)
                .font(.title3).fontWeight(.bold)
                .multilineTextAlignment(.center)
                .padding(.bottom, 6)

            // Description
            if let desc = plugin.description, !desc.isEmpty {
                Text(desc)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .lineLimit(3)
                    .padding(.bottom, 8)
            }

            // Slug badge
            Text(plugin.slug)
                .font(.caption2)
                .foregroundStyle(.tertiary)
                .padding(.horizontal, 10).padding(.vertical, 4)
                .background(Color.primary.opacity(0.06))
                .clipShape(Capsule())
                .padding(.bottom, 20)

            // Install button
            Button {
                guard !isConfirmInstalling else { return }
                isConfirmInstalling = true
                Task {
                    let ok = await installPlugin(plugin: plugin)
                    isConfirmInstalling = false
                    if ok { selectedPlugin = nil }
                }
            } label: {
                HStack(spacing: 8) {
                    if isConfirmInstalling {
                        ProgressView().tint(.white).scaleEffect(0.85)
                    } else {
                        Image(systemName: "arrow.down.circle.fill")
                    }
                    Text(isConfirmInstalling
                         ? lang.t("インストール中...", en: "Installing...", zh: "安装中...", ko: "설치 중...")
                         : lang.t("インストール",     en: "Install",       zh: "安装",     ko: "설치"))
                        .fontWeight(.semibold)
                }
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(isConfirmInstalling ? BrandConfig.brand.opacity(0.6) : BrandConfig.brand)
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .disabled(isConfirmInstalling)
        }
        .padding(24)
        .frame(width: min(UIScreen.main.bounds.width - 48, 360))
        .background(BrandConfig.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 22))
        .shadow(color: .black.opacity(0.25), radius: 24, y: 8)
    }

    // MARK: - Templates tab

    private var templatesTab: some View {
        Group {
            if popularService.isLoading && popularService.plugins.isEmpty {
                Spacer()
                ProgressView()
                Spacer()
            } else if let err = popularService.errorMessage, popularService.plugins.isEmpty {
                emptyState(
                    icon: "wifi.slash",
                    title: lang.t("接続エラー",      en: "Connection Error", zh: "连接错误", ko: "연결 오류"),
                    subtitle: err
                )
            } else if popularService.plugins.isEmpty {
                emptyState(
                    icon: "tray",
                    title: lang.t("スキルが見つかりません", en: "No Skills Found",    zh: "未找到技能",       ko: "스킬 없음"),
                    subtitle: lang.t("しばらくしてからもう一度お試しください", en: "Please try again later", zh: "请稍后重试", ko: "나중에 다시 시도해주세요")
                )
            } else {
                ScrollView {
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                        ForEach(popularService.plugins) { plugin in
                            ClawHubTemplateCard(plugin: plugin) {
                                selectedPlugin = plugin
                            }
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.bottom, 24)
                }
            }
        }
        .task {
            if popularService.plugins.isEmpty && !popularService.isLoading {
                await popularService.searchPopular(limit: 10)
            }
        }
    }

    // MARK: - Plugins tab

    private var pluginsTab: some View {
        VStack(spacing: 0) {
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField(lang.t("プラグインを検索...", en: "Search plugins...", zh: "搜索插件...", ko: "플러그인 검색..."), text: $searchText)
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

            if clawHubService.isLoading && clawHubService.plugins.isEmpty {
                Spacer()
                ProgressView()
                Spacer()
            } else if let err = clawHubService.errorMessage, clawHubService.plugins.isEmpty {
                emptyState(
                    icon: "wifi.slash",
                    title: lang.t("接続エラー",      en: "Connection Error", zh: "连接错误", ko: "연결 오류"),
                    subtitle: err
                )
            } else if clawHubService.plugins.isEmpty {
                emptyState(
                    icon: "tray",
                    title: lang.t("プラグインが見つかりません", en: "No plugins found",         zh: "未找到插件",       ko: "플러그인 없음"),
                    subtitle: lang.t("別のキーワードで検索してみてください",          en: "Try a different keyword", zh: "请尝试其他关键词", ko: "다른 키워드로 검색해보세요")
                )
            } else {
                ScrollView {
                    LazyVStack(spacing: 10) {
                        ForEach(clawHubService.plugins) { plugin in
                            PluginCard(plugin: plugin) {
                                selectedPlugin = plugin
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

    @discardableResult
    private func installPlugin(plugin: ClawHubPlugin) async -> Bool {
        guard let agentId = agentService.agents.first?.id else {
            showToast(
                lang.t("まずエージェントを作成してください",
                        en: "Please create an agent first",
                        zh: "请先创建一个助手",
                        ko: "먼저 에이전트를 만들어주세요"),
                isError: true
            )
            return false
        }
        do {
            try await clawHubService.install(agentId: agentId, slug: plugin.slug)
            showToast(
                "✅ \(plugin.name) \(lang.t("をインストールしました", en: "installed", zh: "已安装", ko: "설치됨"))",
                isError: false
            )
            await pluginsStore.fetch(agentId: agentId)
            return true
        } catch {
            showToast("⚠️ \(error.localizedDescription)", isError: true)
            return false
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

    private func iconForPlugin(_ p: ClawHubPlugin) -> String {
        let name = p.name.lowercased()
        let slug = p.slug.lowercased()
        let combined = name + " " + slug
        if combined.contains("writ") || combined.contains("copy") { return "✍️" }
        if combined.contains("code") || combined.contains("dev") || combined.contains("git") { return "💻" }
        if combined.contains("data") || combined.contains("analy") { return "📊" }
        if combined.contains("translat") || combined.contains("lang") { return "🌐" }
        if combined.contains("research") || combined.contains("search") { return "🔍" }
        if combined.contains("business") || combined.contains("meet") || combined.contains("email") { return "💼" }
        if combined.contains("agent") { return "🤖" }
        if combined.contains("assistant") { return "🧠" }
        if combined.contains("image") || combined.contains("art") || combined.contains("design") { return "🎨" }
        if combined.contains("music") || combined.contains("audio") { return "🎵" }
        if combined.contains("video") || combined.contains("stream") { return "🎬" }
        return "🔌"
    }

    @ViewBuilder
    private func emptyState(icon: String, title: String, subtitle: String) -> some View {
        VStack(spacing: 12) {
            Spacer()
            Image(systemName: icon)
                .font(.system(size: 40))
                .foregroundStyle(.secondary)
            Text(title).font(.headline)
            Text(subtitle)
                .font(.footnote)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            Spacer()
        }
    }
}

// MARK: - ClawHub Template Card (grid layout)

private struct ClawHubTemplateCard: View {
    let plugin: ClawHubPlugin
    let onTap: () -> Void

    @Environment(\.lang) var lang

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(iconForPlugin(plugin))
                    .font(.largeTitle)
                Spacer()
                if let dl = plugin.downloads {
                    Label(formatDownloads(dl), systemImage: "arrow.down.circle")
                        .font(.caption2).foregroundStyle(.secondary)
                }
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(plugin.name)
                    .font(.footnote).fontWeight(.semibold).lineLimit(2)
                if let desc = plugin.description, !desc.isEmpty {
                    Text(desc)
                        .font(.caption).foregroundStyle(.secondary).lineLimit(2)
                }
            }

            if let author = plugin.author, !author.isEmpty {
                Text(author)
                    .font(.caption2).foregroundStyle(.tertiary)
            }

            Spacer()

            Button {
                onTap()
            } label: {
                HStack(spacing: 4) {
                    Image(systemName: "plus").font(.caption.bold())
                    Text(lang.t("インストール", en: "Install", zh: "安装", ko: "설치"))
                        .font(.caption).fontWeight(.medium)
                }
                .foregroundStyle(BrandConfig.brand)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .background(BrandConfig.brand.opacity(0.09))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
        }
        .padding(14)
        .frame(height: 180)
        .background(BrandConfig.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .shadow(color: .black.opacity(0.04), radius: 6, y: 2)
    }

    private func iconForPlugin(_ p: ClawHubPlugin) -> String {
        let name = p.name.lowercased()
        let slug = p.slug.lowercased()
        let combined = name + " " + slug
        if combined.contains("writ") || combined.contains("copy") { return "✍️" }
        if combined.contains("code") || combined.contains("dev") || combined.contains("git") { return "💻" }
        if combined.contains("data") || combined.contains("analy") { return "📊" }
        if combined.contains("translat") || combined.contains("lang") { return "🌐" }
        if combined.contains("research") || combined.contains("search") { return "🔍" }
        if combined.contains("business") || combined.contains("meet") || combined.contains("email") { return "💼" }
        if combined.contains("agent") { return "🤖" }
        if combined.contains("assistant") { return "🧠" }
        if combined.contains("image") || combined.contains("art") || combined.contains("design") { return "🎨" }
        if combined.contains("music") || combined.contains("audio") { return "🎵" }
        if combined.contains("video") || combined.contains("stream") { return "🎬" }
        return "🔌"
    }

    private func formatDownloads(_ n: Int) -> String {
        n >= 1000 ? "\(n / 1000)k" : "\(n)"
    }
}

// MARK: - Plugin card

private struct PluginCard: View {
    let plugin: ClawHubPlugin
    let onTap: () -> Void

    @Environment(\.lang) var lang

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 3) {
                    Text(plugin.name)
                        .font(.subheadline).fontWeight(.semibold)
                    if let author = plugin.author {
                        Text(author).font(.caption).foregroundStyle(.secondary)
                    }
                }
                Spacer()
                installButton
            }

            if let desc = plugin.description, !desc.isEmpty {
                Text(desc)
                    .font(.caption).foregroundStyle(.secondary).lineLimit(2)
            }

            HStack(spacing: 10) {
                if let version = plugin.version {
                    Label(version, systemImage: "tag")
                        .font(.caption2).foregroundStyle(.secondary)
                }
                if let dl = plugin.downloads {
                    Label(formatDownloads(dl), systemImage: "arrow.down.circle")
                        .font(.caption2).foregroundStyle(.secondary)
                }
                if let tags = plugin.tags, let first = tags.first {
                    Text(first)
                        .font(.caption2).fontWeight(.medium)
                        .foregroundStyle(BrandConfig.brand)
                        .padding(.horizontal, 6).padding(.vertical, 2)
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
    }

    @ViewBuilder
    private var installButton: some View {
        Button {
            onTap()
        } label: {
            HStack(spacing: 4) {
                Image(systemName: "arrow.down.circle")
                    .font(.caption.bold())
                Text(lang.t("インストール", en: "Install", zh: "安装", ko: "설치"))
                    .font(.caption).fontWeight(.medium)
            }
            .foregroundStyle(BrandConfig.brand)
            .frame(minWidth: 80)
            .padding(.vertical, 6).padding(.horizontal, 10)
            .background(BrandConfig.brand.opacity(0.09))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
    }

    private func formatDownloads(_ n: Int) -> String {
        n >= 1000 ? "\(n / 1000)k" : "\(n)"
    }
}

// MARK: - Toast

private struct ToastView: View {
    let message: String
    let isError: Bool

    var body: some View {
        Text(message)
            .font(.footnote).fontWeight(.medium)
            .foregroundStyle(.white)
            .padding(.horizontal, 16).padding(.vertical, 10)
            .background(isError ? Color.red.opacity(0.9) : Color.green.opacity(0.85))
            .clipShape(Capsule())
            .shadow(color: .black.opacity(0.15), radius: 8, y: 4)
    }
}
