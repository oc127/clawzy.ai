import SwiftUI

struct WelcomeView: View {
    @State private var showLogin    = false
    @State private var showRegister = false
    @State private var appeared     = false

    var body: some View {
        ZStack {
            // ── Background ──────────────────────────────
            Color(white: 0.04).ignoresSafeArea()

            // Glow blobs
            GeometryReader { geo in
                let w = geo.size.width
                let h = geo.size.height

                // Top-right red blob
                Circle()
                    .fill(BrandConfig.brand.opacity(0.55))
                    .frame(width: w * 0.75)
                    .blur(radius: 80)
                    .offset(x: w * 0.35, y: -h * 0.08)

                // Bottom-left deep red blob
                Circle()
                    .fill(BrandConfig.brandDeep.opacity(0.45))
                    .frame(width: w * 0.65)
                    .blur(radius: 90)
                    .offset(x: -w * 0.2, y: h * 0.55)
            }
            .ignoresSafeArea()

            // ── Content ─────────────────────────────────
            VStack(alignment: .leading, spacing: 0) {
                // Logo mark
                ZStack {
                    RoundedRectangle(cornerRadius: 14)
                        .fill(Color.white.opacity(0.12))
                        .frame(width: 52, height: 52)
                    Text("N")
                        .font(.system(size: 26, weight: .bold, design: .rounded))
                        .foregroundStyle(.white)
                }
                .padding(.top, 64)
                .padding(.bottom, 40)
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 20)

                // Headline
                VStack(alignment: .leading, spacing: 8) {
                    Text("あなたの")
                        .font(.system(size: 42, weight: .bold))
                        .foregroundStyle(.white)
                    Text("AIエージェント")
                        .font(.system(size: 42, weight: .bold))
                        .foregroundStyle(Color(red: 1.0, green: 0.42, blue: 0.42))
                    Text("を、自由に。")
                        .font(.system(size: 42, weight: .bold))
                        .foregroundStyle(.white)
                }
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 30)

                Spacer()

                // Buttons
                HStack(spacing: 12) {
                    // Secondary — Register
                    Button {
                        showRegister = true
                    } label: {
                        Text("新規登録")
                            .font(.body)
                            .fontWeight(.medium)
                            .foregroundStyle(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 16)
                            .background(Color.white.opacity(0.14))
                            .clipShape(Capsule())
                    }

                    // Primary — Login
                    Button {
                        showLogin = true
                    } label: {
                        HStack(spacing: 6) {
                            Text("ログイン")
                                .font(.body)
                                .fontWeight(.semibold)
                            Image(systemName: "arrow.up.right")
                                .font(.footnote.bold())
                        }
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .background(BrandConfig.brand)
                        .clipShape(Capsule())
                    }
                }
                .padding(.bottom, 52)
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 24)
            }
            .padding(.horizontal, 28)
        }
        .onAppear {
            withAnimation(.spring(duration: 0.7, bounce: 0.2).delay(0.1)) {
                appeared = true
            }
        }
        .sheet(isPresented: $showLogin) {
            LoginView()
        }
        .sheet(isPresented: $showRegister) {
            RegisterView()
        }
    }
}
