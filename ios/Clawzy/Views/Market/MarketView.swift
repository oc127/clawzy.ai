import SwiftUI

// MARK: - MarketView

struct MarketView: View {
    @Environment(AgentService.self) var agentService
    @Environment(\.lang) var lang
    @State private var templates: [AppTemplate] = []
    @State private var isLoading = true
    @State private var selectedCategory = ""
    @State private var toastMessage: String? = nil

    private var allLabel: String { lang.t("すべて", en: "All", zh: "全部", ko: "전체") }

    var categories: [String] {
        let cats = templates.map(\.category)
        var seen = Set<String>()
        let unique = cats.filter { seen.insert($0).inserted }
        return [allLabel] + unique
    }

    var filtered: [AppTemplate] {
        selectedCategory == allLabel || selectedCategory.isEmpty
            ? templates
            : templates.filter { $0.category == selectedCategory }
    }

    var body: some View {
        NavigationStack {
            ZStack(alignment: .bottom) {
                Group {
                    if isLoading {
                        skeletonGrid
                    } else if templates.isEmpty {
                        emptyState
                    } else {
                        templateGrid
                    }
                }
                .background(BrandConfig.backgroundColor)
                .navigationTitle(lang.t("マーケット", en: "Market", zh: "市场", ko: "마켓"))
                .task { await loadTemplates() }
                .refreshable { await loadTemplates() }

                if let msg = toastMessage {
                    Text(msg)
                        .font(.footnote).fontWeight(.medium)
                        .foregroundStyle(.white)
                        .padding(.horizontal, 20).padding(.vertical, 12)
                        .background(Color.black.opacity(0.75))
                        .clipShape(Capsule())
                        .padding(.bottom, 20)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
            .animation(.easeInOut(duration: 0.3), value: toastMessage)
        }
    }

    // MARK: - Template grid

    private var templateGrid: some View {
        ScrollView {
            VStack(spacing: 0) {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(categories, id: \.self) { cat in
                            Button { withAnimation { selectedCategory = cat } } label: {
                                Text(cat == allLabel ? allLabel : lang.categoryLabel(cat))
                                    .font(.footnote).fontWeight(.medium)
                                    .foregroundStyle(selectedCategory == cat ? .white : .primary)
                                    .padding(.horizontal, 14).padding(.vertical, 8)
                                    .background(selectedCategory == cat ? BrandConfig.brand : BrandConfig.disabledGray)
                                    .clipShape(Capsule())
                            }
                        }
                    }
                    .padding(.horizontal, 16).padding(.vertical, 12)
                }

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                    ForEach(filtered) { t in
                        TemplateCard(template: t, agentService: agentService) { msg in
                            showToast(msg)
                        }
                    }
                }
                .padding(.horizontal, 16).padding(.bottom, 24)
            }
        }
    }

    // MARK: - Skeleton loader

    private var skeletonGrid: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                ForEach(0..<6, id: \.self) { _ in
                    RoundedRectangle(cornerRadius: 14)
                        .fill(BrandConfig.disabledGray)
                        .frame(height: 180)
                        .shimmer()
                }
            }
            .padding(16)
        }
    }

    // MARK: - Empty state

    private var emptyState: some View {
        VStack(spacing: 16) {
            Spacer()
            Image(systemName: "storefront")
                .font(.system(size: 48))
                .foregroundStyle(Color(white: 0.8))
            Text(lang.t("テンプレートがありません", en: "No templates", zh: "暂无模板", ko: "템플릿 없음"))
                .foregroundStyle(.secondary)
            Button(lang.t("再読み込み", en: "Reload", zh: "重新加载", ko: "다시 로드")) {
                Task { await loadTemplates() }
            }
            .foregroundStyle(BrandConfig.brand)
            Spacer()
        }
    }

    // MARK: - Helpers

    private func loadTemplates() async {
        isLoading = true
        // Also ensure agents are loaded so alreadyAdded check works
        if agentService.agents.isEmpty { await agentService.fetchAgents() }
        let remote: [AppTemplate]? = try? await APIClient.shared.request(Constants.API.templates)
        if let remote, !remote.isEmpty {
            templates = remote
        } else {
            templates = Self.fallbackTemplates
        }
        isLoading = false
    }

    private func showToast(_ msg: String) {
        withAnimation { toastMessage = msg }
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            withAnimation { toastMessage = nil }
        }
    }

    // Hardcoded fallback — used until server migration runs
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

    /// Localized name/description for fallback templates by ID.
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
}

// MARK: - Template card

private struct TemplateCard: View {
    let template: AppTemplate
    let agentService: AgentService
    let onAdded: (String) -> Void

    @State private var isLoading = false
    @Environment(\.lang) var lang

    var alreadyAdded: Bool {
        agentService.agents.contains { $0.name == template.name }
    }

    /// Returns localized name, falling back to template.name (Japanese from server)
    var localizedName: String {
        guard let l10n = MarketView.templateL10n[template.id] else { return template.name }
        return lang.t(template.name, en: l10n.name.en, zh: l10n.name.zh, ko: l10n.name.ko)
    }

    /// Returns localized description, falling back to template.description
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

            Button {
                guard !alreadyAdded && !isLoading else { return }
                isLoading = true
                Task {
                    let result = await agentService.createAgent(
                        name: template.name,
                        modelName: template.modelName,
                        systemPrompt: template.systemPrompt.isEmpty ? nil : template.systemPrompt
                    )
                    isLoading = false
                    if result != nil {
                        onAdded("\(template.icon) \(localizedName) \(lang.t("を追加しました", en: "added", zh: "已添加", ko: "추가됨"))")
                    } else {
                        let errMsg = agentService.errorMessage ?? lang.t("エラーが発生しました", en: "Something went wrong", zh: "出现错误", ko: "오류가 발생했습니다")
                        onAdded("⚠️ \(errMsg)")
                    }
                }
            } label: {
                HStack(spacing: 4) {
                    if isLoading {
                        ProgressView().scaleEffect(0.7).tint(BrandConfig.brand)
                    } else {
                        Image(systemName: alreadyAdded ? "checkmark" : "plus").font(.caption.bold())
                    }
                    Text(alreadyAdded
                         ? lang.t("追加済み", en: "Added",     zh: "已添加", ko: "추가됨")
                         : lang.t("追加する",  en: "Add Agent", zh: "添加",   ko: "추가"))
                        .font(.caption).fontWeight(.medium)
                }
                .foregroundStyle(alreadyAdded ? .secondary : BrandConfig.brand)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .background(alreadyAdded ? BrandConfig.disabledGray : BrandConfig.brand.opacity(0.09))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .disabled(alreadyAdded || isLoading)
        }
        .padding(14)
        .frame(height: 180)
        .background(BrandConfig.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .shadow(color: .black.opacity(0.04), radius: 6, y: 2)
    }
}

// MARK: - Shimmer effect

private struct ShimmerModifier: ViewModifier {
    @State private var phase: CGFloat = -1

    func body(content: Content) -> some View {
        content
            .overlay(
                GeometryReader { geo in
                    LinearGradient(
                        colors: [.clear, .white.opacity(0.5), .clear],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                    .frame(width: geo.size.width * 2)
                    .offset(x: geo.size.width * phase)
                    .animation(.linear(duration: 1.2).repeatForever(autoreverses: false), value: phase)
                }
                .clipped()
            )
            .onAppear { phase = 1 }
    }
}

private extension View {
    func shimmer() -> some View {
        modifier(ShimmerModifier())
    }
}
