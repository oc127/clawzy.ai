import SwiftUI

struct MainTabView: View {
    @State private var agentService = AgentService()
    @Environment(\.lang) var lang

    var body: some View {
        TabView {
            DashboardView()
                .tabItem { Label(lang.t("ホーム", en: "Home", zh: "首页", ko: "홈"), systemImage: "house") }

            MarketView()
                .tabItem { Label(lang.t("マーケット", en: "Market", zh: "市场", ko: "마켓"), systemImage: "storefront") }

            SettingsView()
                .tabItem { Label(lang.t("設定", en: "Settings", zh: "设置", ko: "설정"), systemImage: "gearshape") }
        }
        .tint(BrandConfig.brand)
        .environment(agentService)
    }
}
