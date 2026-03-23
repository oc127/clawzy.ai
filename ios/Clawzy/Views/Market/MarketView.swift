import SwiftUI

struct MarketView: View {
    @State private var selectedCategory = 0

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
            ScrollView {
                VStack(spacing: 0) {
                    // Category scroll
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
                                                : Color(white: 0.92)
                                        )
                                        .clipShape(Capsule())
                                }
                            }
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                    }

                    // Template grid
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                        ForEach(templates) { t in
                            TemplateCard(template: t)
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.bottom, 24)
                }
            }
            .background(BrandConfig.backgroundColor)
            .navigationTitle("マーケット")
        }
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
                    await service.createAgent(name: template.name, modelName: template.model)
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
                .background(added ? Color(white: 0.93) : BrandConfig.brand.opacity(0.09))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .disabled(added)
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
