import SwiftUI

struct MarketView: View {
    @Environment(AgentService.self) var agentService
    @Environment(PluginsStore.self) var pluginsStore
    @Environment(\.lang) var lang

    @State private var selectedTab = 0
    @State private var clawHubService = ClawHubService()
    @State private var searchText = ""
    @State private var searchTask: Task<Void, Never>?

    // Plugin popup state
    @State private var selectedPlugin: ClawHubPlugin?
    @State private var isConfirmInstalling = false

    // Character state
    @State private var characters: [CharacterTemplate] = []
    @State private var isLoadingCharacters = true
    @State private var selectedCharacter: CharacterTemplate?
    @State private var isConfirmUsingChar = false

    // Toast state
    @State private var toastMessage: String?
    @State private var toastIsError = false

    var body: some View {
        ZStack(alignment: .top) {
            NavigationStack {
                VStack(spacing: 0) {
                    // Tab switcher
                    HStack(spacing: 0) {
                        TabSwitchButton(
                            title: lang.t("タスク", en: "Skills", zh: "技能", ko: "스킬"),
                            isSelected: selectedTab == 0
                        ) { withAnimation { selectedTab = 0 } }
                        TabSwitchButton(
                            title: lang.t("ロールプレイ", en: "Role Play", zh: "角色扮演", ko: "롤플레이"),
                            isSelected: selectedTab == 1
                        ) { withAnimation { selectedTab = 1 } }
                    }
                    .padding(.horizontal, 16)
                    .padding(.top, 8)
                    .padding(.bottom, 4)

                    if selectedTab == 0 {
                        skillsTab
                    } else {
                        roleplayTab
                    }
                }
                .background(Color(UIColor.systemBackground))
                .navigationTitle(lang.t("マーケット", en: "Market", zh: "市场", ko: "마켓"))
                .overlay(alignment: .bottom) {
                    if let msg = toastMessage {
                        ToastView(message: msg, isError: toastIsError)
                            .transition(.move(edge: .bottom).combined(with: .opacity))
                            .padding(.bottom, 100)
                    }
                }
                .animation(.easeInOut(duration: 0.25), value: toastMessage)
            }

            // Plugin popup
            if let plugin = selectedPlugin {
                Color.black.opacity(0.5)
                    .ignoresSafeArea()
                    .onTapGesture {
                        if !isConfirmInstalling { selectedPlugin = nil }
                    }
                pluginPopupCard(plugin: plugin)
                    .padding(.top, 80)
            }

            // Character popup
            if let character = selectedCharacter {
                Color.black.opacity(0.5)
                    .ignoresSafeArea()
                    .onTapGesture {
                        if !isConfirmUsingChar { selectedCharacter = nil }
                    }
                characterPopupCard(character: character)
                    .padding(.top, 80)
            }
        }
        .animation(.spring(response: 0.28, dampingFraction: 0.82), value: selectedPlugin != nil)
        .animation(.spring(response: 0.28, dampingFraction: 0.82), value: selectedCharacter != nil)
        .onChange(of: selectedTab) { _, newVal in
            if newVal == 0 && clawHubService.plugins.isEmpty {
                Task { await clawHubService.search(lang: lang.current) }
            }
            if newVal == 1 && characters.isEmpty {
                Task { await loadCharacters() }
            }
        }
    }

    // MARK: - Skills Tab

    private var skillsTab: some View {
        VStack(spacing: 0) {
            // Search bar
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField(lang.t("スキルを検索...", en: "Search skills...", zh: "搜索技能...", ko: "스킬 검색..."), text: $searchText)
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
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .background(Color(UIColor.systemGray6))
            .clipShape(RoundedRectangle(cornerRadius: 20))
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .onChange(of: searchText) { _, _ in triggerSearch() }

            if clawHubService.isLoading && clawHubService.plugins.isEmpty {
                Spacer()
                ProgressView()
                Spacer()
            } else if let err = clawHubService.errorMessage, clawHubService.plugins.isEmpty {
                emptyState(
                    icon: "wifi.slash",
                    title: lang.t("接続エラー", en: "Connection Error", zh: "连接错误", ko: "연결 오류"),
                    subtitle: err
                )
            } else if clawHubService.plugins.isEmpty {
                emptyState(
                    icon: "tray",
                    title: lang.t("スキルが見つかりません", en: "No skills found", zh: "未找到技能", ko: "스킬 없음"),
                    subtitle: lang.t("別のキーワードで検索してみてください", en: "Try a different keyword", zh: "请尝试其他关键词", ko: "다른 키워드로 검색해보세요")
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
        .task {
            if clawHubService.plugins.isEmpty {
                await clawHubService.search(lang: lang.current)
            }
        }
    }

    // MARK: - Roleplay Tab

    private var roleplayTab: some View {
        Group {
            if isLoadingCharacters {
                characterSkeletonGrid
            } else if characters.isEmpty {
                emptyState(
                    icon: "person.2",
                    title: lang.t("キャラクターがありません", en: "No characters yet", zh: "暂无角色", ko: "캐릭터 없음"),
                    subtitle: lang.t("しばらくしてからもう一度お試しください", en: "Please try again later", zh: "请稍后重试", ko: "나중에 다시 시도해주세요")
                )
            } else {
                ScrollView {
                    LazyVGrid(
                        columns: [GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12)],
                        spacing: 12
                    ) {
                        ForEach(characters) { char in
                            CharacterCard(character: char) {
                                selectedCharacter = char
                            }
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.top, 12)
                    .padding(.bottom, 100)
                }
            }
        }
        .task {
            if characters.isEmpty {
                await loadCharacters()
            }
        }
    }

    private var characterSkeletonGrid: some View {
        ScrollView {
            LazyVGrid(
                columns: [GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12)],
                spacing: 12
            ) {
                ForEach(0..<6, id: \.self) { _ in
                    RoundedRectangle(cornerRadius: 20)
                        .fill(Color(UIColor.systemGray5))
                        .frame(height: 200)
                }
            }
            .padding(16)
        }
    }

    // MARK: - Plugin popup card

    @ViewBuilder
    private func pluginPopupCard(plugin: ClawHubPlugin) -> some View {
        VStack(spacing: 0) {
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

            Text(iconForPlugin(plugin))
                .font(.system(size: 52))
                .padding(.bottom, 12)

            Text(plugin.name)
                .font(.title3).fontWeight(.bold)
                .multilineTextAlignment(.center)
                .padding(.bottom, 6)

            if let desc = plugin.description, !desc.isEmpty {
                Text(desc)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .lineLimit(3)
                    .padding(.bottom, 8)
            }

            Text(plugin.slug)
                .font(.caption2)
                .foregroundStyle(.tertiary)
                .padding(.horizontal, 10).padding(.vertical, 4)
                .background(Color.primary.opacity(0.06))
                .clipShape(Capsule())
                .padding(.bottom, 20)

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
                        ProgressView().tint(Color.white).scaleEffect(0.85)
                    } else {
                        Image(systemName: "arrow.down.circle.fill")
                    }
                    Text(isConfirmInstalling
                         ? lang.t("インストール中...", en: "Installing...", zh: "安装中...", ko: "설치 중...")
                         : lang.t("インストール",     en: "Install",       zh: "安装",     ko: "설치"))
                        .fontWeight(.semibold)
                }
                .foregroundStyle(Color.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(isConfirmInstalling ? BrandConfig.brand.opacity(0.6) : BrandConfig.brand)
                .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .disabled(isConfirmInstalling)
        }
        .padding(24)
        .frame(width: 320)
        .background(Color(UIColor.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 24))
        .shadow(color: .black.opacity(0.20), radius: 28, y: 10)
    }

    // MARK: - Character popup card

    @ViewBuilder
    private func characterPopupCard(character: CharacterTemplate) -> some View {
        let accentColor = Color(hex: character.avatarColor ?? "#888888") ?? BrandConfig.brand

        VStack(spacing: 0) {
            HStack {
                Spacer()
                Button {
                    if !isConfirmUsingChar { selectedCharacter = nil }
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title2)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.bottom, 8)

            // Avatar
            CharacterAvatar(character: character, size: 72)
                .padding(.bottom, 12)

            Text(character.name)
                .font(.title3).fontWeight(.bold)
            if let reading = character.nameReading {
                Text(reading)
                    .font(.caption).foregroundStyle(.secondary)
                    .padding(.bottom, 4)
            }

            if let occ = character.occupation {
                Text(occ)
                    .font(.subheadline).foregroundStyle(.secondary)
                    .padding(.bottom, 8)
            }

            if let greeting = character.greetingMessage {
                Text("「\(greeting)」")
                    .font(.footnote).italic()
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .lineLimit(3)
                    .padding(.horizontal, 8)
                    .padding(.bottom, 12)
            }

            // Category chip
            Text(character.category)
                .font(.caption2).fontWeight(.semibold)
                .foregroundStyle(accentColor)
                .padding(.horizontal, 10).padding(.vertical, 4)
                .background(accentColor.opacity(0.12))
                .clipShape(Capsule())
                .padding(.bottom, 20)

            Button {
                guard !isConfirmUsingChar else { return }
                isConfirmUsingChar = true
                Task {
                    let ok = await useCharacter(character: character)
                    isConfirmUsingChar = false
                    if ok { selectedCharacter = nil }
                }
            } label: {
                HStack(spacing: 8) {
                    if isConfirmUsingChar {
                        ProgressView().tint(Color.white).scaleEffect(0.85)
                    } else {
                        Image(systemName: "person.fill.badge.plus")
                    }
                    Text(isConfirmUsingChar
                         ? lang.t("作成中...", en: "Creating...", zh: "创建中...", ko: "생성 중...")
                         : lang.t("チャット開始", en: "Start Chat", zh: "开始聊天", ko: "채팅 시작"))
                        .fontWeight(.semibold)
                }
                .foregroundStyle(Color.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(isConfirmUsingChar ? accentColor.opacity(0.6) : accentColor)
                .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .disabled(isConfirmUsingChar)
        }
        .padding(24)
        .frame(width: 320)
        .background(Color(UIColor.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 24))
        .shadow(color: .black.opacity(0.20), radius: 28, y: 10)
    }

    // MARK: - Helpers

    private func loadCharacters() async {
        isLoadingCharacters = true
        defer { isLoadingCharacters = false }
        if let remote: [CharacterTemplate] = try? await APIClient.shared.request(Constants.API.characters) {
            characters = remote
        }
    }

    @discardableResult
    private func useCharacter(character: CharacterTemplate) async -> Bool {
        do {
            let _: UseCharacterResponse = try await APIClient.shared.request(
                Constants.API.characterUse(character.id),
                method: "POST"
            )
            await agentService.fetchAgents()
            showToast("\(character.name) \(lang.t("を追加しました", en: "added", zh: "已添加", ko: "추가됨"))")
            return true
        } catch {
            showToast("⚠️ \(error.localizedDescription)", isError: true)
            return false
        }
    }

    private func triggerSearch() {
        searchTask?.cancel()
        searchTask = Task {
            try? await Task.sleep(for: .milliseconds(350))
            guard !Task.isCancelled else { return }
            await clawHubService.search(query: searchText, lang: lang.current)
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
                "\(plugin.name) \(lang.t("をインストールしました", en: "installed", zh: "已安装", ko: "설치됨"))"
            )
            await pluginsStore.fetch(agentId: agentId)
            return true
        } catch {
            showToast("⚠️ \(error.localizedDescription)", isError: true)
            return false
        }
    }

    private func showToast(_ message: String, isError: Bool = false) {
        toastMessage = message
        toastIsError = isError
        Task {
            try? await Task.sleep(for: .seconds(3))
            toastMessage = nil
        }
    }

    private func iconForPlugin(_ p: ClawHubPlugin) -> String {
        let combined = (p.name + " " + p.slug).lowercased()
        if combined.contains("writ") || combined.contains("copy") { return "✍️" }
        if combined.contains("code") || combined.contains("dev") || combined.contains("git") { return "💻" }
        if combined.contains("data") || combined.contains("analy") { return "📊" }
        if combined.contains("translat") || combined.contains("lang") { return "🌐" }
        if combined.contains("research") || combined.contains("search") { return "🔍" }
        if combined.contains("business") || combined.contains("meet") || combined.contains("email") { return "💼" }
        if combined.contains("image") || combined.contains("art") || combined.contains("design") { return "🎨" }
        if combined.contains("music") || combined.contains("audio") { return "🎵" }
        if combined.contains("video") || combined.contains("stream") { return "🎬" }
        if combined.contains("agent") { return "🤖" }
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

// MARK: - Tab switch button

private struct TabSwitchButton: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.subheadline).fontWeight(.semibold)
                .foregroundStyle(isSelected ? BrandConfig.brand : .secondary)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(
                    VStack {
                        Spacer()
                        if isSelected {
                            BrandConfig.brand
                                .frame(height: 2)
                                .clipShape(Capsule())
                        } else {
                            Color.clear.frame(height: 2)
                        }
                    }
                )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Character Avatar

struct CharacterAvatar: View {
    let character: CharacterTemplate
    let size: CGFloat

    private var accent: Color {
        Color(hex: character.avatarColor ?? "#888888") ?? .gray
    }

    private var initial: String {
        String(character.name.prefix(1))
    }

    var body: some View {
        ZStack {
            Circle()
                .fill(
                    LinearGradient(
                        colors: [accent, accent.opacity(0.6)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: size, height: size)

            Text(initial)
                .font(.system(size: size * 0.42, weight: .bold, design: .rounded))
                .foregroundStyle(.white)
        }
        .shadow(color: accent.opacity(0.35), radius: size * 0.15, y: size * 0.06)
    }
}

// MARK: - Character Card

private struct CharacterCard: View {
    let character: CharacterTemplate
    let onTap: () -> Void

    private var accent: Color {
        Color(hex: character.avatarColor ?? "#888888") ?? .gray
    }

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .center, spacing: 10) {
                CharacterAvatar(character: character, size: 56)

                VStack(spacing: 2) {
                    HStack(spacing: 4) {
                        Text(character.name)
                            .font(.footnote).fontWeight(.bold)
                        if let reading = character.nameReading {
                            Text(reading)
                                .font(.caption2).foregroundStyle(.secondary)
                        }
                    }
                    if let occ = character.occupation {
                        Text(occ)
                            .font(.caption2).foregroundStyle(.secondary).lineLimit(1)
                    }
                }

                if let greeting = character.greetingMessage {
                    Text(greeting)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .lineLimit(2)
                        .frame(maxWidth: .infinity)
                }

                Spacer(minLength: 0)

                Text(character.category)
                    .font(.caption2).fontWeight(.semibold)
                    .foregroundStyle(accent)
                    .padding(.horizontal, 8).padding(.vertical, 3)
                    .background(accent.opacity(0.12))
                    .clipShape(Capsule())
            }
            .padding(14)
            .frame(height: 200)
            .frame(maxWidth: .infinity)
            .background(Color(UIColor.systemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 20))
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(accent.opacity(0.25), lineWidth: 1)
            )
            .shadow(color: accent.opacity(0.08), radius: 8, x: 0, y: 4)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Plugin Card

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
                Button { onTap() } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "arrow.down.circle").font(.caption.bold())
                        Text(lang.t("インストール", en: "Install", zh: "安装", ko: "설치"))
                            .font(.caption).fontWeight(.semibold)
                    }
                    .foregroundStyle(Color.white)
                    .frame(minWidth: 80)
                    .padding(.vertical, 6).padding(.horizontal, 10)
                    .background(BrandConfig.brand)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                }
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
                    Label(dl >= 1000 ? "\(dl / 1000)k" : "\(dl)", systemImage: "arrow.down.circle")
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
        .padding(16)
        .background(Color(UIColor.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color(UIColor.separator), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.04), radius: 6, x: 0, y: 3)
    }
}

// MARK: - Toast

private struct ToastView: View {
    let message: String
    let isError: Bool

    var body: some View {
        Text(message)
            .font(.footnote).fontWeight(.medium)
            .foregroundStyle(Color.white)
            .padding(.horizontal, 16).padding(.vertical, 10)
            .background(isError ? Color.red.opacity(0.9) : Color.green.opacity(0.85))
            .clipShape(Capsule())
            .shadow(color: .black.opacity(0.15), radius: 8, y: 4)
    }
}

// MARK: - Color(hex:) extension

extension Color {
    init?(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        guard hex.count == 6, let value = UInt64(hex, radix: 16) else { return nil }
        let r = Double((value >> 16) & 0xFF) / 255
        let g = Double((value >> 8) & 0xFF) / 255
        let b = Double(value & 0xFF) / 255
        self.init(red: r, green: g, blue: b)
    }
}
