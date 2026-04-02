import SwiftUI

struct RegisterView: View {
    @Environment(AuthManager.self) var authManager
    @Environment(\.dismiss) var dismiss
    @Environment(\.lang) var lang

    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""

    private var passwordsMatch: Bool {
        !password.isEmpty && password == confirmPassword
    }

    private var canSubmit: Bool {
        !name.isEmpty && !email.isEmpty && passwordsMatch && !authManager.isLoading
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 0) {
                    HStack(spacing: 10) {
                        NipponLogo(size: 44)
                        Text(BrandConfig.appName)
                            .font(.title2)
                            .fontWeight(.bold)
                    }
                    .padding(.top, 56)
                    .padding(.bottom, 32)

                    VStack(alignment: .leading, spacing: 20) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(lang.t("アカウント作成", en: "Create Account", zh: "创建账号", ko: "계정 만들기"))
                                .font(.largeTitle)
                                .fontWeight(.bold)
                            Text(lang.t("登録で 500 クレジットプレゼント", en: "Get 500 free credits on signup", zh: "注册即送500积分", ko: "가입 시 500 크레딧 증정"))
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

                        LabeledField(label: lang.t("ニックネーム", en: "Nickname", zh: "昵称", ko: "닉네임")) {
                            TextField("", text: $name)
                                .textFieldStyle(.plain)
                                .textContentType(.name)
                                .autocorrectionDisabled()
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
                                .textContentType(.newPassword)
                        }

                        LabeledField(label: lang.t("パスワード（確認）", en: "Confirm Password", zh: "确认密码", ko: "비밀번호 확인")) {
                            SecureField("", text: $confirmPassword)
                                .textFieldStyle(.plain)
                                .textContentType(.newPassword)
                        }

                        if !confirmPassword.isEmpty && !passwordsMatch {
                            Text(lang.t("パスワードが一致しません", en: "Passwords do not match", zh: "密码不匹配", ko: "비밀번호가 일치하지 않습니다"))
                                .font(.caption)
                                .foregroundStyle(BrandConfig.brand)
                        }

                        BrandButton(title: lang.t("新規登録", en: "Register", zh: "注册", ko: "회원가입"), isLoading: authManager.isLoading) {
                            Task {
                                await authManager.register(name: name, email: email, password: password)
                                if authManager.isAuthenticated { dismiss() }
                            }
                        }
                        .disabled(!canSubmit)
                        .padding(.top, 4)

                        HStack {
                            Spacer()
                            Button {
                                dismiss()
                            } label: {
                                HStack(spacing: 4) {
                                    Text(lang.t("すでにアカウントがある？", en: "Already have an account?", zh: "已有账号？", ko: "이미 계정이 있으신가요?"))
                                        .foregroundStyle(.secondary)
                                    Text(lang.t("ログイン", en: "Login", zh: "登录", ko: "로그인"))
                                        .foregroundStyle(BrandConfig.brand)
                                }
                                .font(.footnote)
                            }
                            Spacer()
                        }
                    }
                    .padding(.horizontal, 28)
                    .padding(.bottom, 48)
                }
            }
            .background(BrandConfig.backgroundColor)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(lang.t("閉じる", en: "Close", zh: "关闭", ko: "닫기")) { dismiss() }
                        .foregroundStyle(BrandConfig.brand)
                }
            }
        }
    }
}
