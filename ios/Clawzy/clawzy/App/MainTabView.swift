import SwiftUI

struct MainTabView: View {
    @State private var agentService = AgentService()

    var body: some View {
        TabView {
            DashboardView()
                .tabItem { Label("ホーム", systemImage: "house") }

            MarketView()
                .tabItem { Label("マーケット", systemImage: "storefront") }

            SettingsView()
                .tabItem { Label("設定", systemImage: "gearshape") }
        }
        .tint(BrandConfig.brand)
        .environment(agentService)
    }
}
