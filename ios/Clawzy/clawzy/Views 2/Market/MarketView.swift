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

    // Template popup state
    @State private var selectedTemplate: AppTemplate?
    @State private var isConfirmAdding = false

    // Templates state
    @State private var templates: [AppTemplate] = []
    @State private var isLoadingTemplates = true
    @State private var selectedCategory = ""

    // Toast state
    @State private var toastMessage: String?
    @State private var toastIsError = false

    private var allLabel: String { lang.t("すべて", en: "All", zh: "全部", ko: "전체") }

    private var categories: [String] {
        let cats = templates.map(\.category)
        var seen = Set<String>()
        let unique = cats.filter { seen.insert($0).inserted }
        return [allLabel] + unique
    }

    private var filteredTemplates: [AppTemplate] {
        selectedCategory == allLabel || selectedCategory.isEmpty
            ? templates
            : templates.filter { $0.category == selectedCategory }
    }

    var body: some View {
        ZStack(alignment: .top) {
            NavigationStack {
                VStack(spacing: 0) {
                    // Tab switcher
                    HStack(spacing: 0) {
                        TabSwitchButton(
                            title: lang.t("テンプレート", en: "Templates", zh: "模板", ko: "템플릿"),
                            isSelected: selectedTab == 0
                        ) { withAnimation { selectedTab = 0 } }
                        TabSwitchButton(
                            title: lang.t("プラグイン", en: "Plugins", zh: "插件", ko: "플러그인"),
                            isSelected: selectedTab == 1
                        ) { withAnimation { selectedTab = 1 } }
                    }
                    .padding(.horizontal, 16)
                    .padding(.top, 8)
                    .padding(.bottom, 4)

                    if selectedTab == 0 {
                        templatesTab
                    } else {
                        pluginsTab
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
                popupCard(plugin: plugin)
                    .padding(.top, 80)
            }

            // Template popup
            if let template = selectedTemplate {
                Color.black.opacity(0.5)
                    .ignoresSafeArea()
                    .onTapGesture {
                        if !isConfirmAdding { selectedTemplate = nil }
                    }
                templatePopupCard(template: template)
                    .padding(.top, 80)
            }
        }
        .animation(.spring(response: 0.28, dampingFraction: 0.82), value: selectedPlugin != nil)
        .animation(.spring(response: 0.28, dampingFraction: 0.82), value: selectedTemplate != nil)
        .onChange(of: selectedTab) { _, newVal in
            if newVal == 1 && clawHubService.plugins.isEmpty {
                Task { await clawHubService.search(lang: lang.current) }
            }
        }
    }

    // MARK: - Tab switch button

    // MARK: - Popup card (plugin)

    @ViewBuilder
    private func popupCard(plugin: ClawHubPlugin) -> some View {
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

    // MARK: - Popup card (template)

    @ViewBuilder
    private func templatePopupCard(template: AppTemplate) -> some View {
        let l10n = Self.templateL10n[template.id]
        let localName = l10n != nil ? lang.t(template.name, en: l10n!.name.en, zh: l10n!.name.zh, ko: l10n!.name.ko) : template.name
        let localDesc = l10n != nil ? lang.t(template.description, en: l10n!.desc.en, zh: l10n!.desc.zh, ko: l10n!.desc.ko) : template.description

        VStack(spacing: 0) {
            HStack {
                Spacer()
                Button {
                    if !isConfirmAdding { selectedTemplate = nil }
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title2)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.bottom, 8)

            Text(template.icon)
                .font(.system(size: 52))
                .padding(.bottom, 12)

            Text(localName)
                .font(.title3).fontWeight(.bold)
                .multilineTextAlignment(.center)
                .padding(.bottom, 6)

            Text(localDesc)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .lineLimit(3)
                .padding(.bottom, 8)

            Text(lang.categoryLabel(template.category))
                .font(.caption2).fontWeight(.semibold)
                .foregroundStyle(BrandConfig.brand)
                .padding(.horizontal, 10).padding(.vertical, 4)
                .background(BrandConfig.brand.opacity(0.10))
                .clipShape(Capsule())
                .padding(.bottom, 20)

            Button {
                guard !isConfirmAdding else { return }
                isConfirmAdding = true
                Task {
                    let result = await agentService.createAgent(
                        name: template.name,
                        modelName: template.modelName,
                        systemPrompt: template.systemPrompt.isEmpty ? nil : template.systemPrompt
                    )
                    isConfirmAdding = false
                    if result != nil {
                        selectedTemplate = nil
                        showToast("\(template.icon) \(localName) \(lang.t("を追加しました", en: "added", zh: "已添加", ko: "추가됨"))")
                    } else {
                        let errMsg = agentService.errorMessage ?? lang.t("エラーが発生しました", en: "Something went wrong", zh: "出现错误", ko: "오류가 발생했습니다")
                        showToast("⚠️ \(errMsg)", isError: true)
                    }
                }
            } label: {
                HStack(spacing: 8) {
                    if isConfirmAdding {
                        ProgressView().tint(Color.white).scaleEffect(0.85)
                    } else {
                        Image(systemName: "plus.circle.fill")
                    }
                    Text(isConfirmAdding
                         ? lang.t("作成中...", en: "Creating...", zh: "创建中...", ko: "생성 중...")
                         : lang.t("追加する", en: "Add Agent",   zh: "添加助手", ko: "에이전트 추가"))
                        .fontWeight(.semibold)
                }
                .foregroundStyle(Color.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(isConfirmAdding ? BrandConfig.brand.opacity(0.6) : BrandConfig.brand)
                .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .disabled(isConfirmAdding)
        }
        .padding(24)
        .frame(width: 320)
        .background(Color(UIColor.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 24))
        .shadow(color: .black.opacity(0.20), radius: 28, y: 10)
    }

    // MARK: - Templates tab

    private var templatesTab: some View {
        Group {
            if isLoadingTemplates {
                skeletonGrid
            } else if templates.isEmpty {
                emptyState(
                    icon: "storefront",
                    title: lang.t("テンプレートがありません", en: "No templates", zh: "暂无模板", ko: "템플릿 없음"),
                    subtitle: lang.t("しばらくしてからもう一度お試しください", en: "Please try again later", zh: "请稍后重试", ko: "나중에 다시 시도해주세요")
                )
            } else {
                ScrollView {
                    VStack(spacing: 0) {
                        // Category chips
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                ForEach(categories, id: \.self) { cat in
                                    Button { withAnimation { selectedCategory = cat } } label: {
                                        let isSelected = selectedCategory == cat || (selectedCategory.isEmpty && cat == allLabel)
                                        Text(cat == allLabel ? allLabel : lang.categoryLabel(cat))
                                            .font(.footnote).fontWeight(.semibold)
                                            .foregroundStyle(isSelected ? Color.white : .primary)
                                            .padding(.horizontal, 16).padding(.vertical, 8)
                                            .background(isSelected ? BrandConfig.brand : Color(UIColor.systemGray5))
                                            .clipShape(Capsule())
                                    }
                                }
                            }
                            .padding(.horizontal, 16).padding(.vertical, 12)
                        }

                        LazyVGrid(columns: [GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12)], spacing: 12) {
                            ForEach(filteredTemplates) { t in
                                TemplateCard(template: t, agentService: agentService) {
                                    selectedTemplate = t
                                }
                            }
                        }
                        .padding(.horizontal, 16).padding(.bottom, 100)
                    }
                }
            }
        }
        .task {
            if templates.isEmpty {
                await loadTemplates()
            }
        }
    }

    private var skeletonGrid: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12)], spacing: 12) {
                ForEach(0..<6, id: \.self) { _ in
                    RoundedRectangle(cornerRadius: 20)
                        .fill(Color(UIColor.systemGray5))
                        .frame(height: 180)
                }
            }
            .padding(16)
        }
    }

    private func loadTemplates() async {
        isLoadingTemplates = true
        if agentService.agents.isEmpty { await agentService.fetchAgents() }
        let remote: [AppTemplate]? = try? await APIClient.shared.request(Constants.API.templates)
        templates = (remote != nil && !remote!.isEmpty) ? remote! : Self.fallbackTemplates
        isLoadingTemplates = false
    }

    static let fallbackTemplates: [AppTemplate] = [
        AppTemplate(id: "tpl-001", name: "ビジネスアシスタント", description: "メール・資料作成・会議サポート",      icon: "💼", category: "ビジネス", modelName: "deepseek-chat",     systemPrompt: "あなたはプロフェッショナルなビジネスアシスタントです。", sortOrder: 1),
        AppTemplate(id: "tpl-002", name: "日本語家庭教師",      description: "日本語学習をサポートします",          icon: "📚", category: "教育",     modelName: "qwen-plus",          systemPrompt: "あなたは経験豊富な日本語教師です。",                    sortOrder: 2),
        AppTemplate(id: "tpl-003", name: "コピーライター",      description: "広告・SNS・ブログ文章を作成",         icon: "✍️", category: "創作",     modelName: "deepseek-chat",     systemPrompt: "あなたはクリエイティブなコピーライターです。",            sortOrder: 3),
        AppTemplate(id: "tpl-004", name: "データアナリスト",    description: "データ分析・レポート作成",             icon: "📊", category: "分析",     modelName: "deepseek-reasoner", systemPrompt: "あなたはデータアナリストです。",                        sortOrder: 4),
        AppTemplate(id: "tpl-005", name: "コードレビュアー",    description: "コードレビュー・バグ修正サポート",     icon: "💻", category: "コード",   modelName: "deepseek-chat",     systemPrompt: "あなたはシニアエンジニアです。",                        sortOrder: 5),
        AppTemplate(id: "tpl-006", name: "クリエイティブライター", description: "小説・詩・脚本の執筆サポート",     icon: "🎨", category: "創作",     modelName: "qwen-max",          systemPrompt: "あなたはクリエイティブライターです。",                  sortOrder: 6),
        AppTemplate(id: "tpl-007", name: "翻訳スペシャリスト",  description: "日英中韓の高精度翻訳",               icon: "🌐", category: "ビジネス", modelName: "qwen-plus",          systemPrompt: "あなたはプロの翻訳者です。",                            sortOrder: 7),
        AppTemplate(id: "tpl-008", name: "リサーチアシスタント", description: "調査・要約・情報整理",              icon: "🔍", category: "分析",     modelName: "deepseek-reasoner", systemPrompt: "あなたはリサーチアシスタントです。",                    sortOrder: 8),
    ]

    static let templateL10n: [String: (name: (en: String, zh: String, ko: String), desc: (en: String, zh: String, ko: String))] = [
        "tpl-001": (name: (en: "Business Assistant",    zh: "商务助手",    ko: "비즈니스 어시스턴트"),
                    desc: (en: "Email, documents & meeting support", zh: "邮件、文档和会议支持", ko: "이메일, 문서, 회의 지원")),
        "tpl-002": (name: (en: "Language Tutor",        zh: "语言家教",    ko: "언어 튜터"),
                    desc: (en: "Learn Japanese with an expert tutor", zh: "与专业教师学习日语", ko: "전문 강사와 일본어 학습")),
        "tpl-003": (name: (en: "Copywriter",            zh: "文案写手",    ko: "카피라이터"),
                    desc: (en: "Ads, social media & blog writing",    zh: "广告、社交媒体和博客文案", ko: "광고, SNS, 블로그 글쓰기")),
        "tpl-004": (name: (en: "Data Analyst",          zh: "数据分析师",  ko: "데이터 분석가"),
                    desc: (en: "Data analysis & report generation",   zh: "数据分析和报告生成", ko: "데이터 분석 및 보고서 작성")),
        "tpl-005": (name: (en: "Code Reviewer",         zh: "代码审查员",  ko: "코드 리뷰어"),
                    desc: (en: "Code review & bug-fix assistance",    zh: "代码审查和错误修复", ko: "코드 리뷰 및 버그 수정")),
        "tpl-006": (name: (en: "Creative Writer",       zh: "创意写作者",  ko: "크리에이티브 라이터"),
                    desc: (en: "Novels, poetry & screenplay writing", zh: "小说、诗歌和剧本写作", ko: "소설, 시, 대본 창작")),
        "tpl-007": (name: (en: "Translation Specialist", zh: "翻译专家",   ko: "번역 전문가"),
                    desc: (en: "High-accuracy JA/EN/ZH/KO translation", zh: "日英中韩高精度翻译", ko: "일/영/중/한 고품질 번역")),
        "tpl-008": (name: (en: "Research Assistant",   zh: "研究助手",    ko: "리서치 어시스턴트"),
                    desc: (en: "Research, summary & information organisation", zh: "调研、总结和信息整理", ko: "조사, 요약 및 정보 정리")),
    ]

    // MARK: - Plugins tab

    private var pluginsTab: some View {
        VStack(spacing: 0) {
            // Search bar
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
                    title: lang.t("接続エラー",      en: "Connection Error", zh: "连接错误", ko: "연결 오류"),
                    subtitle: err
                )
            } else if clawHubService.plugins.isEmpty {
                emptyState(
                    icon: "tray",
                    title: lang.t("プラグインが見つかりません", en: "No plugins found",         zh: "未找到插件",       ko: "플러그인 없음"),
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
    }

    // MARK: - Helpers

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
                "\(plugin.name) \(lang.t("をインストールしました", en: "installed", zh: "已安装", ko: "설치됨"))",
                isError: false
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

// MARK: - Template Card

private struct TemplateCard: View {
    let template: AppTemplate
    let agentService: AgentService
    let onTap: () -> Void

    @Environment(\.lang) var lang

    var alreadyAdded: Bool {
        agentService.agents.contains { $0.name == template.name }
    }

    var localizedName: String {
        guard let l10n = MarketView.templateL10n[template.id] else { return template.name }
        return lang.t(template.name, en: l10n.name.en, zh: l10n.name.zh, ko: l10n.name.ko)
    }

    var localizedDescription: String {
        guard let l10n = MarketView.templateL10n[template.id] else { return template.description }
        return lang.t(template.description, en: l10n.desc.en, zh: l10n.desc.zh, ko: l10n.desc.ko)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(template.icon).font(.largeTitle)
                Spacer()
                Text(lang.categoryLabel(template.category))
                    .font(.caption2).fontWeight(.semibold)
                    .foregroundStyle(BrandConfig.brand)
                    .padding(.horizontal, 6).padding(.vertical, 3)
                    .background(BrandConfig.brand.opacity(0.10))
                    .clipShape(Capsule())
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(localizedName)
                    .font(.footnote).fontWeight(.semibold).lineLimit(1)
                Text(localizedDescription)
                    .font(.caption).foregroundStyle(.secondary).lineLimit(2)
            }

            Spacer()

            Button { onTap() } label: {
                HStack(spacing: 4) {
                    Image(systemName: alreadyAdded ? "checkmark" : "plus").font(.caption.bold())
                    Text(alreadyAdded
                         ? lang.t("追加済み", en: "Added",     zh: "已添加", ko: "추가됨")
                         : lang.t("追加する",  en: "Add Agent", zh: "添加",   ko: "추가"))
                        .font(.caption).fontWeight(.medium)
                }
                .foregroundStyle(alreadyAdded ? .secondary : Color.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .background(alreadyAdded ? Color(UIColor.systemGray5) : BrandConfig.brand)
                .clipShape(RoundedRectangle(cornerRadius: 10))
            }
            .disabled(alreadyAdded)
        }
        .padding(14)
        .frame(height: 180)
        .background(Color(UIColor.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color(UIColor.separator), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 4)
    }
}

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
