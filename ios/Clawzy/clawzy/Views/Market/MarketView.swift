import SwiftUI

struct MarketView: View {
    @Environment(AgentService.self) var agentService
    @Environment(\.lang) var lang

    @State private var selectedTab = 0
    @State private var selectedCategory = 0
    @State private var clawHubService = ClawHubService()
    @State private var searchText = ""
    @State private var searchTask: Task<Void, Never>?
    @State private var installedAgent: Agent?

    // Toast state
    @State private var toastMessage: String?
    @State private var toastIsError = false

    // Category keys (Japanese as canonical key, localized on display)
    let categoryKeys = ["すべて", "ビジネス", "教育", "創作", "分析", "コード"]

    let templates: [AgentTemplate] = [
        AgentTemplate(icon: "💼", name: "ビジネスアシスタント",   desc: "メール・資料作成・会議サポート",       model: "deepseek-chat",     tag: "ビジネス", systemPrompt: "あなたはプロフェッショナルなビジネスアシスタントです。メール作成、資料作成、会議のサポートを行います。"),
        AgentTemplate(icon: "📚", name: "日本語家庭教師",         desc: "日本語学習をサポートします",           model: "qwen-plus",          tag: "教育",     systemPrompt: "あなたは経験豊富な日本語教師です。"),
        AgentTemplate(icon: "✍️", name: "コピーライター",         desc: "広告・SNS・ブログ文章を作成",          model: "deepseek-chat",     tag: "創作",     systemPrompt: "あなたはクリエイティブなコピーライターです。"),
        AgentTemplate(icon: "📊", name: "データアナリスト",       desc: "データ分析・レポート作成",              model: "deepseek-reasoner", tag: "分析",     systemPrompt: "あなたはデータアナリストです。"),
        AgentTemplate(icon: "💻", name: "コードレビュアー",       desc: "コードレビュー・バグ修正サポート",      model: "deepseek-chat",     tag: "コード",   systemPrompt: "あなたはシニアエンジニアです。コードレビューとバグ修正をサポートします。"),
        AgentTemplate(icon: "🎨", name: "クリエイティブライター", desc: "小説・詩・脚本の執筆サポート",          model: "qwen-max",          tag: "創作",     systemPrompt: "あなたはクリエイティブライターです。小説、詩、脚本の執筆をサポートします。"),
        AgentTemplate(icon: "🌐", name: "翻訳スペシャリスト",     desc: "日英中韓の高精度翻訳",                 model: "qwen-plus",          tag: "ビジネス", systemPrompt: "あなたはプロの翻訳者です。日英中韓の翻訳を高精度で行います。"),
        AgentTemplate(icon: "🔍", name: "リサーチアシスタント",   desc: "調査・要約・情報整理",                 model: "deepseek-reasoner", tag: "分析",     systemPrompt: "あなたはリサーチアシスタントです。調査、要約、情報整理を行います。"),
    ]

    /// Localized name / description keyed by Japanese name.
    static let templateL10n: [String: (name: (en: String, zh: String, ko: String), desc: (en: String, zh: String, ko: String))] = [
        "ビジネスアシスタント":   (name: (en: "Business Assistant",      zh: "商务助手",    ko: "비즈니스 어시스턴트"),
                                   desc: (en: "Email, documents & meeting support",        zh: "邮件、文档和会议支持",    ko: "이메일, 문서, 회의 지원")),
        "日本語家庭教師":         (name: (en: "Language Tutor",           zh: "语言家教",    ko: "언어 튜터"),
                                   desc: (en: "Learn Japanese with an expert tutor",       zh: "与专业教师学习日语",      ko: "전문 강사와 일본어 학습")),
        "コピーライター":         (name: (en: "Copywriter",               zh: "文案写手",    ko: "카피라이터"),
                                   desc: (en: "Ads, social media & blog writing",          zh: "广告、社交媒体和博客文案", ko: "광고, SNS, 블로그 글쓰기")),
        "データアナリスト":       (name: (en: "Data Analyst",             zh: "数据分析师",  ko: "데이터 분석가"),
                                   desc: (en: "Data analysis & report generation",         zh: "数据分析和报告生成",      ko: "데이터 분석 및 보고서 작성")),
        "コードレビュアー":       (name: (en: "Code Reviewer",            zh: "代码审查员",  ko: "코드 리뷰어"),
                                   desc: (en: "Code review & bug-fix assistance",          zh: "代码审查和错误修复",      ko: "코드 리뷰 및 버그 수정")),
        "クリエイティブライター": (name: (en: "Creative Writer",          zh: "创意写作者",  ko: "크리에이티브 라이터"),
                                   desc: (en: "Novels, poetry & screenplay writing",       zh: "小说、诗歌和剧本写作",    ko: "소설, 시, 대본 창작")),
        "翻訳スペシャリスト":     (name: (en: "Translation Specialist",   zh: "翻译专家",    ko: "번역 전문가"),
                                   desc: (en: "High-accuracy JA/EN/ZH/KO translation",    zh: "日英中韩高精度翻译",      ko: "일/영/중/한 고품질 번역")),
        "リサーチアシスタント":   (name: (en: "Research Assistant",       zh: "研究助手",    ko: "리서치 어시스턴트"),
                                   desc: (en: "Research, summary & info organisation",    zh: "调研、总结和信息整理",    ko: "조사, 요약 및 정보 정리")),
    ]

    var filteredTemplates: [AgentTemplate] {
        if selectedCategory == 0 { return templates }
        let cat = categoryKeys[selectedCategory]
        return templates.filter { $0.tag == cat }
    }

    var body: some View {
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
            // Navigate to ChatView after successful install
            .navigationDestination(isPresented: Binding(
                get: { installedAgent != nil },
                set: { if !$0 { installedAgent = nil } }
            )) {
                if let agent = installedAgent {
                    ChatView(agent: agent)
                }
            }
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
                        ForEach(categoryKeys.indices, id: \.self) { i in
                            Button {
                                selectedCategory = i
                            } label: {
                                Text(i == 0
                                     ? lang.t("すべて", en: "All", zh: "全部", ko: "전체")
                                     : lang.categoryLabel(categoryKeys[i]))
                                    .font(.footnote)
                                    .fontWeight(.medium)
                                    .foregroundStyle(selectedCategory == i ? .white : .primary)
                                    .padding(.horizontal, 14)
                                    .padding(.vertical, 8)
                                    .background(selectedCategory == i ? BrandConfig.brand : BrandConfig.disabledGray)
                                    .clipShape(Capsule())
                            }
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                }

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                    ForEach(filteredTemplates) { t in
                        TemplateCard(template: t, agentService: agentService) { agent in
                            let name = localizedTemplateName(t)
                            showToast(
                                "✅ \(name) \(lang.t("を追加しました。開いています...", en: "added, opening...", zh: "已添加，正在打开...", ko: "추가됨, 열리는 중..."))",
                                isError: false
                            )
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
                                installedAgent = agent
                            }
                        } onError: { errMsg in
                            showToast("⚠️ \(errMsg)", isError: true)
                        }
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

    private func localizedTemplateName(_ t: AgentTemplate) -> String {
        guard let l10n = Self.templateL10n[t.name] else { return t.name }
        return lang.t(t.name, en: l10n.name.en, zh: l10n.name.zh, ko: l10n.name.ko)
    }

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
            showToast(
                "✅ \(plugin.name) \(lang.t("をインストールしました。開いています...", en: "installed, opening...", zh: "已安装，正在打开...", ko: "설치됨, 열리는 중..."))",
                isError: false
            )
            if let agent = agentService.agents.first(where: { $0.id == agentId }) {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
                    installedAgent = agent
                }
            }
        } catch {
            showToast("⚠️ \(error.localizedDescription)", isError: true)
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

// MARK: - Template card

private struct TemplateCard: View {
    let template: AgentTemplate
    let agentService: AgentService
    let onInstalled: (Agent) -> Void
    let onError: (String) -> Void

    @State private var isLoading = false
    @State private var added = false
    @State private var showConfirm = false
    @Environment(\.lang) var lang

    var localizedName: String {
        guard let l10n = MarketView.templateL10n[template.name] else { return template.name }
        return lang.t(template.name, en: l10n.name.en, zh: l10n.name.zh, ko: l10n.name.ko)
    }

    var localizedDesc: String {
        guard let l10n = MarketView.templateL10n[template.name] else { return template.desc }
        return lang.t(template.desc, en: l10n.desc.en, zh: l10n.desc.zh, ko: l10n.desc.ko)
    }

    var alreadyAdded: Bool {
        agentService.agents.contains { $0.name == template.name }
    }

    var isDisabled: Bool { added || alreadyAdded || isLoading }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(template.icon).font(.largeTitle)
                Spacer()
                Text(lang.categoryLabel(template.tag))
                    .font(.caption2).fontWeight(.semibold)
                    .foregroundStyle(BrandConfig.brand)
                    .padding(.horizontal, 6).padding(.vertical, 3)
                    .background(BrandConfig.brand.opacity(0.10))
                    .clipShape(Capsule())
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(localizedName)
                    .font(.footnote).fontWeight(.semibold).lineLimit(1)
                Text(localizedDesc)
                    .font(.caption).foregroundStyle(.secondary).lineLimit(2)
            }

            Spacer()

            Button {
                guard !isDisabled else { return }
                showConfirm = true
            } label: {
                HStack(spacing: 4) {
                    if isLoading {
                        ProgressView().scaleEffect(0.7).tint(BrandConfig.brand)
                    } else {
                        Image(systemName: isDisabled ? "checkmark" : "plus").font(.caption.bold())
                    }
                    Text(isDisabled
                         ? lang.t("追加済み", en: "Added",     zh: "已添加", ko: "추가됨")
                         : lang.t("追加する",  en: "Add Agent", zh: "添加",   ko: "추가"))
                        .font(.caption).fontWeight(.medium)
                }
                .foregroundStyle(isDisabled ? .secondary : BrandConfig.brand)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .background(isDisabled ? BrandConfig.disabledGray : BrandConfig.brand.opacity(0.09))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .disabled(isDisabled)
        }
        .padding(14)
        .frame(height: 180)
        .background(BrandConfig.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .shadow(color: .black.opacity(0.04), radius: 6, y: 2)
        .sheet(isPresented: $showConfirm) {
            TemplateInstallSheet(
                template: template,
                localizedName: localizedName,
                localizedDesc: localizedDesc,
                onInstall: { doInstall() }
            )
        }
    }

    private func doInstall() {
        isLoading = true
        Task {
            let agent = await agentService.createAgent(
                name: template.name,
                modelName: template.model,
                systemPrompt: template.systemPrompt.isEmpty ? nil : template.systemPrompt
            )
            isLoading = false
            if let agent {
                withAnimation { added = true }
                onInstalled(agent)
            } else {
                let msg = agentService.errorMessage
                    ?? lang.t("エラーが発生しました", en: "Something went wrong", zh: "出现错误", ko: "오류가 발생했습니다")
                onError(msg)
            }
        }
    }
}

// MARK: - Template install sheet

private struct TemplateInstallSheet: View {
    let template: AgentTemplate
    let localizedName: String
    let localizedDesc: String
    let onInstall: () -> Void

    @Environment(\.dismiss) private var dismiss
    @Environment(\.lang) var lang

    var body: some View {
        VStack(spacing: 0) {
            Capsule()
                .fill(Color(UIColor.separator))
                .frame(width: 36, height: 4)
                .padding(.top, 12)
                .padding(.bottom, 20)

            Text(template.icon)
                .font(.system(size: 56))
                .padding(.bottom, 10)

            Text(localizedName)
                .font(.title3).fontWeight(.bold)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)

            Text(localizedDesc)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)
                .padding(.top, 6)

            if !template.systemPrompt.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text(lang.t("システムプロンプト", en: "System Prompt", zh: "系统提示词", ko: "시스템 프롬프트"))
                        .font(.caption).fontWeight(.semibold).foregroundStyle(.secondary)
                    Text(template.systemPrompt)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(4)
                }
                .padding(12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(BrandConfig.disabledGray)
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .padding(.horizontal, 24)
                .padding(.top, 16)
            }

            Spacer()

            VStack(spacing: 10) {
                Button {
                    dismiss()
                    onInstall()
                } label: {
                    Text(lang.t("追加する", en: "Add Agent", zh: "添加助手", ko: "에이전트 추가"))
                        .font(.body).fontWeight(.semibold)
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                        .background(BrandConfig.brand)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }

                Button {
                    dismiss()
                } label: {
                    Text(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소"))
                        .font(.body).fontWeight(.medium)
                        .foregroundStyle(.primary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                        .background(BrandConfig.disabledGray)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }
            }
            .padding(.horizontal, 24)
            .padding(.bottom, 32)
        }
        .background(BrandConfig.cardBackground)
        .presentationDetents([.medium])
    }
}

// MARK: - Plugin card

private struct PluginCard: View {
    let plugin: ClawHubPlugin
    let onInstall: (String) async -> Void

    @State private var showAgentPicker = false
    @State private var isInstalling = false
    @State private var installed = false
    @Environment(AgentService.self) var agentService
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
        .sheet(isPresented: $showAgentPicker) {
            AgentPickerSheet { agentId in
                showAgentPicker = false
                isInstalling = true
                Task {
                    await onInstall(agentId)
                    isInstalling = false
                    installed = true
                }
            }
        }
    }

    @ViewBuilder
    private var installButton: some View {
        Button {
            if !installed && !isInstalling { showAgentPicker = true }
        } label: {
            Group {
                if isInstalling {
                    ProgressView().controlSize(.small).tint(BrandConfig.brand)
                } else {
                    HStack(spacing: 4) {
                        Image(systemName: installed ? "checkmark" : "arrow.down.circle")
                            .font(.caption.bold())
                        Text(installed
                             ? lang.t("済み",          en: "Installed", zh: "已安装", ko: "설치됨")
                             : lang.t("インストール",  en: "Install",   zh: "安装",   ko: "설치"))
                            .font(.caption).fontWeight(.medium)
                    }
                    .foregroundStyle(installed ? .secondary : BrandConfig.brand)
                }
            }
            .frame(minWidth: 80)
            .padding(.vertical, 6).padding(.horizontal, 10)
            .background(installed ? BrandConfig.disabledGray : BrandConfig.brand.opacity(0.09))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .disabled(installed || isInstalling)
    }

    private func formatDownloads(_ n: Int) -> String {
        n >= 1000 ? "\(n / 1000)k" : "\(n)"
    }
}

// MARK: - Agent picker sheet

private struct AgentPickerSheet: View {
    let onSelect: (String) -> Void

    @Environment(\.dismiss) private var dismiss
    @Environment(AgentService.self) var agentService
    @Environment(\.lang) var lang

    var body: some View {
        NavigationStack {
            Group {
                if agentService.agents.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "person.crop.circle.badge.questionmark")
                            .font(.system(size: 40)).foregroundStyle(.secondary)
                        Text(lang.t("エージェントがありません",
                                    en: "No agents yet",
                                    zh: "还没有助手",
                                    ko: "에이전트가 없습니다"))
                            .font(.headline)
                        Text(lang.t("まずダッシュボードでエージェントを作成してください",
                                    en: "Create an agent on the Home tab first",
                                    zh: "请先在首页创建一个助手",
                                    ko: "먼저 홈 탭에서 에이전트를 만들어주세요"))
                            .font(.footnote).foregroundStyle(.secondary)
                            .multilineTextAlignment(.center).padding(.horizontal, 32)
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
                                        .font(.subheadline).fontWeight(.medium).foregroundStyle(.primary)
                                    Text(agent.modelName)
                                        .font(.caption).foregroundStyle(.secondary)
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .font(.caption).foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .navigationTitle(lang.t("インストール先を選択",
                                    en: "Choose an Agent",
                                    zh: "选择安装目标",
                                    ko: "에이전트 선택"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소")) { dismiss() }
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
            .font(.footnote).fontWeight(.medium)
            .foregroundStyle(.white)
            .padding(.horizontal, 16).padding(.vertical, 10)
            .background(isError ? Color.red.opacity(0.9) : Color.green.opacity(0.85))
            .clipShape(Capsule())
            .shadow(color: .black.opacity(0.15), radius: 8, y: 4)
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
    let systemPrompt: String
}
