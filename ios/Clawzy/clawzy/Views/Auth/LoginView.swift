import SwiftUI

struct LoginView: View {
    @Environment(AuthManager.self) var authManager
    @Environment(\.dismiss) var dismiss
    @Environment(\.lang) var lang
    @State private var email = ""
    @State private var password = ""
    @State private var showRegister = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 0) {
                    // Logo
                    HStack(spacing: 10) {
                        LucyLogo(size: 44)
                        Text(BrandConfig.appName)
                            .font(.title2)
                            .fontWeight(.bold)
                    }
                    .padding(.top, 64)
                    .padding(.bottom, 40)

                    // Form area
                    VStack(alignment: .leading, spacing: 20) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(lang.t("おかえりなさい", en: "Welcome back", zh: "欢迎回来", ko: "다시 오신 것을 환영합니다"))
                                .font(.largeTitle)
                                .fontWeight(.bold)
                            Text(lang.t("\(BrandConfig.appName) にログイン", en: "Sign in to \(BrandConfig.appName)", zh: "登录 \(BrandConfig.appName)", ko: "\(BrandConfig.appName)에 로그인"))
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.bottom, 4)

                        if let error = authManager.errorMessage {
                            HStack {
                                Text(error)
                                    .font(.footnote)
                                    .foregroundStyle(BrandConfig.brand)
                                Spacer()
                            }
                            .padding(.horizontal, 14)
                            .padding(.vertical, 10)
                            .background(BrandConfig.brand.opacity(0.07))
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(BrandConfig.brand.opacity(0.25), lineWidth: 1)
                            )
                        }

                        LabeledField(label: lang.t("メール", en: "Email", zh: "邮箱", ko: "이메일")) {
                            TextField("", text: $email)
                                .textFieldStyle(.plain)
                                .textContentType(.emailAddress)
                                .keyboardType(.emailAddress)
                                .autocorrectionDisabled()
                                .onChange(of: email) { _, v in
                                    let low = v.lowercased().trimmingCharacters(in: .whitespaces)
                                    if low != v { email = low }
                                }
                        }

                        LabeledField(label: lang.t("パスワード", en: "Password", zh: "密码", ko: "비밀번호")) {
                            SecureField("", text: $password)
                                .textFieldStyle(.plain)
                                .textContentType(.password)
                        }

                        BrandButton(title: lang.t("ログイン", en: "Login", zh: "登录", ko: "로그인"), isLoading: authManager.isLoading) {
                            Task {
                                await authManager.login(email: email, password: password)
                                if authManager.isAuthenticated { dismiss() }
                            }
                        }
                        .disabled(email.isEmpty || password.isEmpty || authManager.isLoading)
                        .padding(.top, 4)

                        HStack {
                            Spacer()
                            Button {
                                showRegister = true
                            } label: {
                                HStack(spacing: 4) {
                                    Text(lang.t("アカウントがない？", en: "Don't have an account?", zh: "没有账号？", ko: "계정이 없으신가요?"))
                                        .foregroundStyle(.secondary)
                                    Text(lang.t("登録", en: "Register", zh: "注册", ko: "가입"))
                                        .foregroundStyle(BrandConfig.brand)
                                }
                                .font(.footnote)
                            }
                            Spacer()
                        }
                    }
                    .padding(.horizontal, 28)

                    Spacer(minLength: 48)

                    // Stats bar
                    HStack(spacing: 0) {
                        StatBadge(number: "500", label: "Free credits")
                        Rectangle()
                            .fill(BrandConfig.separator)
                            .frame(width: 1, height: 28)
                        StatBadge(number: "6+", label: "AI models")
                        Rectangle()
                            .fill(BrandConfig.separator)
                            .frame(width: 1, height: 28)
                        StatBadge(number: "24/7", label: "Uptime")
                    }
                    .padding(.horizontal, 24)
                    .padding(.bottom, 48)
                }
            }
            .background(BrandConfig.backgroundColor)
            .sheet(isPresented: $showRegister) {
                RegisterView()
            }
        }
    }
}

private struct StatBadge: View {
    let number: String
    let label: String

    var body: some View {
        VStack(spacing: 3) {
            Text(number)
                .font(.title3)
                .fontWeight(.bold)
                .foregroundStyle(BrandConfig.brand)
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
    }
}
