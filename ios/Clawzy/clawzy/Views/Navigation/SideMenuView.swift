import SwiftUI

struct SideMenuView: View {
    @Binding var isShowing: Bool
    @Environment(AuthManager.self) var authManager
    @Environment(\.lang) var lang
    @State private var selectedSection: SideMenuSection? = nil

    enum SideMenuSection: String, CaseIterable {
        case home, market, settings

        func label(_ lang: LanguageManager) -> String {
            switch self {
            case .home:     return lang.t("ホーム",     en: "Home",     zh: "主页", ko: "홈")
            case .market:   return lang.t("マーケット", en: "Market",   zh: "市场", ko: "마켓")
            case .settings: return lang.t("設定",       en: "Settings", zh: "设置", ko: "설정")
            }
        }

        var icon: String {
            switch self {
            case .home:     return "house.fill"
            case .market:   return "storefront.fill"
            case .settings: return "gearshape.fill"
            }
        }
    }

    var body: some View {
        HStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 0) {
                // Lucy header
                VStack(alignment: .leading, spacing: 12) {
                    LucyLogo(size: 52)
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Lucy")
                            .font(.system(size: 22, weight: .bold, design: .rounded))
                            .foregroundStyle(.primary)
                        if let user = authManager.currentUser {
                            Text(user.name)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .padding(.horizontal, 24)
                .padding(.top, 60)
                .padding(.bottom, 28)

                Divider().padding(.horizontal, 16)

                // Menu items
                VStack(spacing: 4) {
                    ForEach(SideMenuSection.allCases, id: \.self) { section in
                        SideMenuRow(
                            icon: section.icon,
                            label: section.label(lang),
                            isActive: selectedSection == section
                        ) {
                            selectedSection = section
                            withAnimation(.spring(response: 0.35, dampingFraction: 0.75)) {
                                isShowing = false
                            }
                        }
                    }
                }
                .padding(.top, 12)

                Spacer()

                // Footer
                VStack(spacing: 4) {
                    Divider().padding(.horizontal, 16)
                    Text("Lucy v1.0")
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                        .padding(.horizontal, 24)
                        .padding(.vertical, 12)
                }
            }
            .frame(width: 280)
            .background(
                Color(UIColor.systemBackground)
                    .shadow(.drop(color: .black.opacity(0.15), radius: 20, x: 8))
            )

            Spacer()
        }
        .ignoresSafeArea()
    }
}

private struct SideMenuRow: View {
    let icon: String
    let label: String
    let isActive: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 14) {
                Image(systemName: icon)
                    .font(.system(size: 17, weight: isActive ? .semibold : .regular))
                    .foregroundStyle(isActive ? BrandConfig.brand : .secondary)
                    .frame(width: 24)
                Text(label)
                    .font(.system(size: 16, weight: isActive ? .semibold : .regular))
                    .foregroundStyle(isActive ? .primary : .secondary)
                Spacer()
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 13)
            .background(
                isActive
                    ? BrandConfig.brand.opacity(0.08)
                    : Color.clear
            )
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .padding(.horizontal, 8)
        }
        .buttonStyle(.plain)
    }
}
