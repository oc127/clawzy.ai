import SwiftUI

struct MarketView: View {
    @Environment(AgentService.self) var agentService
    @State private var selectedCategory = "すべて"
    @State private var toastMessage: String? = nil

    let categories = ["すべて", "ビジネス", "教育", "創作", "分析", "コード"]

    let templates: [AgentTemplate] = [
        AgentTemplate(icon: "💼", name: "ビジネスアシスタント", desc: "メール・資料作成・会議サポート", model: "deepseek-chat", tag: "ビジネス"),
        AgentTemplate(icon: "📚", name: "日本語家庭教師",     desc: "日本語学習をサポートします",   model: "qwen-plus",        tag: "教育"),
        AgentTemplate(icon: "✍️", name: "コピーライター",     desc: "広告・SNS・ブログ文章を作成", model: "deepseek-chat",    tag: "創作"),
        AgentTemplate(icon: "📊", name: "データアナリスト",   desc: "データ分析・レポート作成",     model: "deepseek-reasoner",tag: "分析"),
        AgentTemplate(icon: "💻", name: "コードレビュアー",   desc: "コードレビュー・バグ修正サポート", model: "deepseek-chat", tag: "コード"),
        AgentTemplate(icon: "🎨", name: "クリエイティブライター", desc: "小説・詩・脚本の執筆サポート", model: "qwen-max",    tag: "創作"),
        AgentTemplate(icon: "🌐", name: "翻訳スペシャリスト", desc: "日英中韓の高精度翻訳",         model: "qwen-plus",        tag: "ビジネス"),
        AgentTemplate(icon: "🔍", name: "リサーチアシスタント", desc: "調査・要約・情報整理",        model: "deepseek-reasoner",tag: "分析"),
    ]

    var filtered: [AgentTemplate] {
        selectedCategory == "すべて" ? templates : templates.filter { $0.tag == selectedCategory }
    }

    var body: some View {
        NavigationStack {
            ZStack(alignment: .bottom) {
                ScrollView {
                    VStack(spacing: 0) {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                ForEach(categories, id: \.self) { cat in
                                    Button { selectedCategory = cat } label: {
                                        Text(cat)
                                            .font(.footnote).fontWeight(.medium)
                                            .foregroundStyle(selectedCategory == cat ? .white : .primary)
                                            .padding(.horizontal, 14).padding(.vertical, 8)
                                            .background(selectedCategory == cat ? BrandConfig.brand : Color(white: 0.92))
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
                .background(BrandConfig.backgroundColor)
                .navigationTitle("マーケット")

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

    private func showToast(_ msg: String) {
        withAnimation { toastMessage = msg }
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            withAnimation { toastMessage = nil }
        }
    }
}

// MARK: - Template card

private struct TemplateCard: View {
    let template: AgentTemplate
    let agentService: AgentService
    let onAdded: (String) -> Void

    @State private var isLoading = false

    var alreadyAdded: Bool {
        agentService.agents.contains { $0.name == template.name }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(template.icon).font(.largeTitle)
                Spacer()
                Text(template.tag)
                    .font(.caption2).fontWeight(.semibold)
                    .foregroundStyle(BrandConfig.brand)
                    .padding(.horizontal, 6).padding(.vertical, 3)
                    .background(BrandConfig.brand.opacity(0.10))
                    .clipShape(Capsule())
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(template.name)
                    .font(.footnote).fontWeight(.semibold).lineLimit(1)
                Text(template.desc)
                    .font(.caption).foregroundStyle(.secondary).lineLimit(2)
            }

            Spacer()

            Button {
                guard !alreadyAdded && !isLoading else { return }
                isLoading = true
                Task {
                    let result = await agentService.createAgent(name: template.name, modelName: template.model)
                    isLoading = false
                    if result != nil {
                        onAdded("\(template.icon) \(template.name) を追加しました")
                    }
                }
            } label: {
                HStack(spacing: 4) {
                    if isLoading {
                        ProgressView().scaleEffect(0.7).tint(BrandConfig.brand)
                    } else {
                        Image(systemName: alreadyAdded ? "checkmark" : "plus").font(.caption.bold())
                    }
                    Text(alreadyAdded ? "追加済み" : "追加する")
                        .font(.caption).fontWeight(.medium)
                }
                .foregroundStyle(alreadyAdded ? .secondary : BrandConfig.brand)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .background(alreadyAdded ? Color(white: 0.93) : BrandConfig.brand.opacity(0.09))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .disabled(alreadyAdded || isLoading)
        }
        .padding(14)
        .frame(height: 180)
        .background(Color.white)
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
