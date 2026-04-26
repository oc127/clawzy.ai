import SwiftUI

struct MainTabView: View {
    @State private var agentService = AgentService()
    @State private var pluginsStore = PluginsStore()
    @State private var showSideMenu = false
    @State private var tabBarVisible = true
    @Environment(\.lang) var lang

    var body: some View {
        ZStack(alignment: .leading) {
            ChatHomeView(showMenu: $showSideMenu)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .offset(x: showSideMenu ? 280 : 0)
                .scaleEffect(showSideMenu ? 0.94 : 1.0, anchor: .trailing)
                .animation(.spring(response: 0.35, dampingFraction: 0.82), value: showSideMenu)

            if showSideMenu {
                Color.black.opacity(0.35)
                    .ignoresSafeArea()
                    .onTapGesture {
                        withAnimation(.spring(response: 0.35, dampingFraction: 0.82)) {
                            showSideMenu = false
                        }
                    }
                    .zIndex(10)

                SideMenuView(isShowing: $showSideMenu)
                    .zIndex(11)
                    .transition(.move(edge: .leading))
            }
        }
        .environment(agentService)
        .environment(pluginsStore)
        .environment(\.tabBarVisible, $tabBarVisible)
        .gesture(
            DragGesture()
                .onEnded { value in
                    if value.translation.width > 80 && !showSideMenu {
                        withAnimation(.spring(response: 0.35, dampingFraction: 0.82)) {
                            showSideMenu = true
                        }
                    } else if value.translation.width < -80 && showSideMenu {
                        withAnimation(.spring(response: 0.35, dampingFraction: 0.82)) {
                            showSideMenu = false
                        }
                    }
                }
        )
    }
}
