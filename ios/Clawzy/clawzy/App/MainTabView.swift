import SwiftUI

// MARK: - Tab definition

enum AppTab: Int, CaseIterable {
    case home, market, settings

    func label(_ lang: LanguageManager) -> String {
        switch self {
        case .home:     return lang.t("ホーム",     en: "Home",     zh: "首页", ko: "홈")
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

// MARK: - MainTabView

struct MainTabView: View {
    @State private var agentService = AgentService()
    @State private var selected: AppTab = .home
    @State private var tabBarVisible = true
    @Environment(\.lang) var lang

    var body: some View {
        ZStack(alignment: .bottom) {
            Group {
                switch selected {
                case .home:     DashboardView()
                case .market:   MarketView()
                case .settings: SettingsView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .safeAreaInset(edge: .bottom) {
                Color.clear.frame(height: tabBarVisible ? 80 : 0)
            }

            if tabBarVisible {
                CustomTabBar(selected: $selected)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .ignoresSafeArea(edges: .bottom)
        .environment(agentService)
        .environment(\.tabBarVisible, $tabBarVisible)
    }
}

// MARK: - Custom tab bar

private struct CustomTabBar: View {
    @Binding var selected: AppTab
    @Environment(\.lang) var lang
    @Namespace private var ns

    var body: some View {
        HStack(spacing: 0) {
            ForEach(AppTab.allCases, id: \.self) { tab in
                TabBarItem(tab: tab, selected: $selected, ns: ns)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(
            RoundedRectangle(cornerRadius: 28)
                .fill(.ultraThinMaterial)
                .shadow(color: .black.opacity(0.12), radius: 20, y: 6)
        )
        .padding(.horizontal, 24)
        .padding(.bottom, 20)
    }
}

private struct TabBarItem: View {
    let tab: AppTab
    @Binding var selected: AppTab
    var ns: Namespace.ID
    @Environment(\.lang) var lang

    var isSelected: Bool { selected == tab }

    var body: some View {
        Button {
            withAnimation(.spring(response: 0.35, dampingFraction: 0.75)) {
                selected = tab
            }
        } label: {
            HStack(spacing: 6) {
                Image(systemName: tab.icon)
                    .font(.system(size: 16, weight: isSelected ? .bold : .regular))
                if isSelected {
                    Text(tab.label(lang))
                        .font(.system(size: 13, weight: .semibold))
                        .transition(.asymmetric(
                            insertion: .scale(scale: 0.8).combined(with: .opacity),
                            removal: .scale(scale: 0.8).combined(with: .opacity)
                        ))
                }
            }
            .foregroundStyle(isSelected ? .white : Color(white: 0.5))
            .padding(.horizontal, isSelected ? 16 : 10)
            .padding(.vertical, 10)
            .background {
                if isSelected {
                    Capsule()
                        .fill(BrandConfig.brand)
                        .matchedGeometryEffect(id: "tab_bg", in: ns)
                }
            }
            .frame(maxWidth: isSelected ? .infinity : nil)
        }
        .buttonStyle(.plain)
    }
}
