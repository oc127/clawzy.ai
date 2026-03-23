import SwiftUI

// MARK: - MarketView

struct MarketView: View {
    @Environment(AgentService.self) var agentService
    @State private var templates: [AppTemplate] = []
    @State private var isLoading = true
    @State private var selectedCategory = "すべて"
    @State private var toastMessage: String? = nil

    var categories: [String] {
        let cats = templates.map(\.category)
        var seen = Set<String>()
        let unique = cats.filter { seen.insert($0).inserted }
        return ["すべて"] + unique
    }

    var filtered: [AppTemplate] {
        selectedCategory == "すべて" ? templates : templates.filter { $0.category == selectedCategory }
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
                .navigationTitle("マーケット")
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
    }

    // MARK: - Skeleton loader

    private var skeletonGrid: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                ForEach(0..<6, id: \.self) { _ in
                    RoundedRectangle(cornerRadius: 14)
                        .fill(Color(white: 0.92))
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
            Text("テンプレートがありません")
                .foregroundStyle(.secondary)
            Button("再読み込み") { Task { await loadTemplates() } }
                .foregroundStyle(BrandConfig.brand)
            Spacer()
        }
    }

    // MARK: - Helpers

    private func loadTemplates() async {
        isLoading = true
        templates = (try? await APIClient.shared.request(Constants.API.templates)) ?? []
        isLoading = false
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
    let template: AppTemplate
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
                Text(template.category)
                    .font(.caption2).fontWeight(.semibold)
                    .foregroundStyle(BrandConfig.brand)
                    .padding(.horizontal, 6).padding(.vertical, 3)
                    .background(BrandConfig.brand.opacity(0.10))
                    .clipShape(Capsule())
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(template.name)
                    .font(.footnote).fontWeight(.semibold).lineLimit(1)
                Text(template.description)
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
