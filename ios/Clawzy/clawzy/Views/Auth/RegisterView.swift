import SwiftUI

struct RegisterView: View {
    @Environment(AuthManager.self) var authManager
    @Environment(\.dismiss) var dismiss

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
                            Text("アカウント作成")
                                .font(.largeTitle)
                                .fontWeight(.bold)
                            Text("登録で 500 クレジットプレゼント")
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

                        LabeledField(label: "ニックネーム") {
                            TextField("", text: $name)
                                .textFieldStyle(.plain)
                                .textContentType(.name)
                                .autocorrectionDisabled()
                        }

                        LabeledField(label: "メール") {
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

                        LabeledField(label: "パスワード") {
                            SecureField("", text: $password)
                                .textFieldStyle(.plain)
                                .textContentType(.newPassword)
                        }

                        LabeledField(label: "パスワード（確認）") {
                            SecureField("", text: $confirmPassword)
                                .textFieldStyle(.plain)
                                .textContentType(.newPassword)
                        }

                        if !confirmPassword.isEmpty && !passwordsMatch {
                            Text("パスワードが一致しません")
                                .font(.caption)
                                .foregroundStyle(BrandConfig.brand)
                        }

                        BrandButton(title: "新規登録", isLoading: authManager.isLoading) {
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
                                    Text("すでにアカウントがある？")
                                        .foregroundStyle(.secondary)
                                    Text("ログイン")
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
                    Button("閉じる") { dismiss() }
                        .foregroundStyle(BrandConfig.brand)
                }
            }
        }
    }
}
