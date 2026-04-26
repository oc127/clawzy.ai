import SwiftUI

struct OnboardingView: View {
    @Environment(AuthManager.self) var authManager
    @Environment(\.lang) var lang
    @State private var userName = ""
    @State private var isLoading = false
    @State private var pulseScale: CGFloat = 1.0
    @State private var showContent = false

    var body: some View {
        ZStack {
            // Warm background
            Color(red: 0.980, green: 0.973, blue: 0.961)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                // Lucy sphere with entrance animation
                ZStack {
                    Circle()
                        .fill(BrandConfig.brand.opacity(0.10))
                        .frame(width: 180, height: 180)
                        .blur(radius: 30)
                        .scaleEffect(pulseScale)

                    LucyLogo(size: 100)
                        .scaleEffect(showContent ? 1.0 : 0.4)
                        .opacity(showContent ? 1.0 : 0.0)
                }
                .onAppear {
                    withAnimation(.spring(response: 0.7, dampingFraction: 0.65).delay(0.1)) {
                        showContent = true
                    }
                    withAnimation(.easeInOut(duration: 2.8).repeatForever(autoreverses: true).delay(0.8)) {
                        pulseScale = 1.10
                    }
                }

                Spacer().frame(height: 32)

                // Greeting text
                VStack(spacing: 10) {
                    Text(lang.t("はじめまして！Lucy だよ 🌟",
                                en: "Hey, I'm Lucy 🌟",
                                zh: "你好！我是 Lucy 🌟",
                                ko: "안녕! 나는 Lucy야 🌟"))
                        .font(.system(size: 24, weight: .bold, design: .rounded))
                        .foregroundStyle(.primary)
                        .multilineTextAlignment(.center)

                    Text(lang.t("あなた専属の AI フレンドだよ。\n何でも話しかけてね。",
                                en: "Your personal AI friend.\nAsk me anything.",
                                zh: "你的专属 AI 朋友。\n随时和我聊聊吧。",
                                ko: "나는 네 전용 AI 친구야.\n뭐든지 말해줘."))
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .lineSpacing(4)
                }
                .opacity(showContent ? 1.0 : 0.0)
                .offset(y: showContent ? 0 : 20)
                .animation(.easeOut(duration: 0.5).delay(0.3), value: showContent)

                Spacer().frame(height: 40)

                // Name input
                VStack(alignment: .leading, spacing: 8) {
                    Text(lang.t("あなたの名前を教えて",
                                en: "What's your name?",
                                zh: "请告诉我你的名字",
                                ko: "이름을 알려줘"))
                        .font(.footnote)
                        .fontWeight(.medium)
                        .foregroundStyle(.secondary)
                        .padding(.horizontal, 4)

                    TextField(
                        lang.t("名前（あだ名も OK）",
                               en: "Your name or nickname",
                               zh: "名字或昵称",
                               ko: "이름 또는 닉네임"),
                        text: $userName
                    )
                    .textFieldStyle(.plain)
                    .font(.body)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 14)
                    .background(Color.white)
                    .clipShape(RoundedRectangle(cornerRadius: 14))
                    .shadow(color: .black.opacity(0.06), radius: 8, y: 2)
                }
                .padding(.horizontal, 32)
                .opacity(showContent ? 1.0 : 0.0)
                .animation(.easeOut(duration: 0.5).delay(0.4), value: showContent)

                Spacer().frame(height: 24)

                // Start button
                Button {
                    Task { await startWithLucy() }
                } label: {
                    ZStack {
                        if isLoading {
                            ProgressView().tint(.white)
                        } else {
                            Text(lang.t("始める", en: "Let's Go!", zh: "开始", ko: "시작하기"))
                                .fontWeight(.semibold)
                                .foregroundStyle(.white)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .background(
                        LinearGradient(
                            colors: [BrandConfig.brandLight, BrandConfig.brand],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .shadow(color: BrandConfig.brand.opacity(0.40), radius: 12, y: 4)
                }
                .disabled(isLoading)
                .padding(.horizontal, 32)
                .opacity(showContent ? 1.0 : 0.0)
                .animation(.easeOut(duration: 0.5).delay(0.5), value: showContent)

                Spacer()
            }
        }
    }

    private func startWithLucy() async {
        isLoading = true
        defer { isLoading = false }
        // Call onboarding API to set up Lucy agent
        do {
            struct OnboardingRequest: Encodable { let user_name: String? }
            struct OnboardingResponse: Decodable { let agent_id: String; let agent_name: String; let greeting: String }
            let body = OnboardingRequest(user_name: userName.isEmpty ? nil : userName)
            let _: OnboardingResponse = try await APIClient.shared.request(
                Constants.API.onboardingLucy,
                method: "POST",
                body: body
            )
        } catch {
            // Silent — onboarding failure is non-fatal, user can still proceed
        }
        // Store user name preference if provided
        if !userName.isEmpty {
            UserDefaults.standard.set(userName, forKey: "lucy_user_name")
        }
        // Mark onboarding complete
        UserDefaults.standard.set(true, forKey: "lucy_onboarding_complete")
    }
}
