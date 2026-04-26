import SwiftUI

struct ChatHomeView: View {
    @Binding var showMenu: Bool
    @Environment(AgentService.self) var agentService
    @Environment(AuthManager.self) var authManager
    @Environment(\.lang) var lang
    @State private var inputText = ""
    @State private var navigateToChat: Agent? = nil
    @State private var isCreatingAgent = false
    @State private var pulseScale: CGFloat = 1.0
    @FocusState private var inputFocused: Bool

    var body: some View {
        NavigationStack {
            ZStack {
                // Warm background
                Color(red: 0.980, green: 0.973, blue: 0.961)
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    // Top bar
                    HStack {
                        Button {
                            withAnimation(.spring(response: 0.35, dampingFraction: 0.75)) {
                                showMenu = true
                            }
                        } label: {
                            Image(systemName: "line.3.horizontal")
                                .font(.system(size: 20, weight: .medium))
                                .foregroundStyle(.primary)
                                .frame(width: 44, height: 44)
                        }
                        Spacer()
                        Text("Lucy")
                            .font(.system(size: 17, weight: .semibold))
                        Spacer()
                        // Balance pill
                        if let user = authManager.currentUser {
                            HStack(spacing: 4) {
                                Image(systemName: "bolt.fill")
                                    .font(.system(size: 10, weight: .bold))
                                Text("\(user.creditBalance)")
                                    .font(.caption).fontWeight(.semibold)
                            }
                            .foregroundStyle(BrandConfig.brand)
                            .padding(.horizontal, 10).padding(.vertical, 5)
                            .background(BrandConfig.brand.opacity(0.10))
                            .clipShape(Capsule())
                        } else {
                            Color.clear.frame(width: 44, height: 44)
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 8)

                    Spacer()

                    // Lucy sphere + greeting
                    VStack(spacing: 24) {
                        // Animated glow sphere
                        ZStack {
                            // Background ambient glow
                            Circle()
                                .fill(BrandConfig.brand.opacity(0.12))
                                .frame(width: 160, height: 160)
                                .blur(radius: 30)
                                .scaleEffect(pulseScale)

                            LucyLogo(size: 90)
                                .scaleEffect(pulseScale * 0.98 + 0.02)
                        }
                        .onAppear {
                            withAnimation(
                                .easeInOut(duration: 2.8).repeatForever(autoreverses: true)
                            ) {
                                pulseScale = 1.08
                            }
                        }

                        // Greeting
                        VStack(spacing: 8) {
                            Text("Lucy")
                                .font(.system(size: 28, weight: .bold, design: .rounded))
                                .foregroundStyle(.primary)
                            Text(lang.t("今日はどんな一日にする？",
                                        en: "Hey, what's up?",
                                        zh: "今天想做什么？",
                                        ko: "오늘은 어떤 하루를 만들어볼까?"))
                                .font(.system(size: 17, weight: .medium))
                                .foregroundStyle(.secondary)
                                .multilineTextAlignment(.center)
                        }
                    }

                    Spacer()

                    // Quick action chips
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 10) {
                            ForEach(quickPrompts, id: \.self) { prompt in
                                Button {
                                    inputText = prompt
                                    inputFocused = true
                                } label: {
                                    Text(prompt)
                                        .font(.caption)
                                        .fontWeight(.medium)
                                        .foregroundStyle(BrandConfig.brand)
                                        .padding(.horizontal, 14)
                                        .padding(.vertical, 8)
                                        .background(BrandConfig.brand.opacity(0.08))
                                        .clipShape(Capsule())
                                        .overlay(Capsule().stroke(BrandConfig.brand.opacity(0.20), lineWidth: 1))
                                }
                            }
                        }
                        .padding(.horizontal, 20)
                    }
                    .padding(.bottom, 12)

                    // Input bar
                    HStack(spacing: 10) {
                        TextField(
                            lang.t("Lucy に話しかける...",
                                   en: "Talk to Lucy...",
                                   zh: "和 Lucy 说话...",
                                   ko: "Lucy에게 말하기..."),
                            text: $inputText,
                            axis: .vertical
                        )
                        .textFieldStyle(.plain)
                        .lineLimit(1...4)
                        .focused($inputFocused)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                        .background(Color.white)
                        .clipShape(RoundedRectangle(cornerRadius: 24))
                        .shadow(color: .black.opacity(0.06), radius: 8, y: 2)

                        Button {
                            sendMessage()
                        } label: {
                            Image(systemName: "arrow.up")
                                .font(.system(size: 15, weight: .bold))
                                .foregroundStyle(.white)
                                .frame(width: 42, height: 42)
                                .background(canSend ? BrandConfig.brand : BrandConfig.disabledGray)
                                .clipShape(Circle())
                        }
                        .disabled(!canSend)
                        .animation(.easeInOut(duration: 0.15), value: canSend)
                    }
                    .padding(.horizontal, 16)
                    .padding(.bottom, 20)
                    .background(
                        Color(red: 0.980, green: 0.973, blue: 0.961)
                            .shadow(.inner(color: .black.opacity(0.04), radius: 8, y: -4))
                    )
                }
            }
            .navigationBarHidden(true)
            .navigationDestination(item: $navigateToChat) { agent in
                ChatView(agent: agent)
            }
        }
        .task {
            await agentService.fetchAgents()
        }
    }

    private var canSend: Bool {
        !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isCreatingAgent
    }

    private var quickPrompts: [String] {
        switch lang.current {
        case "en": return ["What can you do?", "Help me write", "Let's brainstorm", "Summarize this"]
        case "zh": return ["你能做什么？", "帮我写作", "一起头脑风暴", "总结这个"]
        case "ko": return ["뭘 할 수 있어?", "글쓰기 도움", "브레인스토밍", "요약해줘"]
        default:   return ["何ができる？", "文章を書いて", "アイデア出し", "これを要約して"]
        }
    }

    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        inputText = ""
        Task { await openLucyChat(with: text) }
    }

    private func openLucyChat(with initialMessage: String? = nil) async {
        // Use existing Lucy agent or first agent
        if let lucy = agentService.agents.first(where: { $0.name == "Lucy" }) ?? agentService.agents.first {
            await MainActor.run { navigateToChat = lucy }
            return
        }
        // Auto-create Lucy agent
        isCreatingAgent = true
        defer { isCreatingAgent = false }
        if let agent = await agentService.createAgent(
            name: "Lucy",
            modelName: "auto",
            systemPrompt: nil
        ) {
            await MainActor.run { navigateToChat = agent }
        }
    }
}
