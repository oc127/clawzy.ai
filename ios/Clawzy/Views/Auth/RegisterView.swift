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

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Text("创建账号")
                    .font(.title)
                    .fontWeight(.bold)

                Text("注册即送 500 积分")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                VStack(spacing: 16) {
                    TextField("昵称", text: $name)
                        .textFieldStyle(.roundedBorder)
                        .textContentType(.name)

                    TextField("邮箱", text: $email)
                        .textFieldStyle(.roundedBorder)
                        .textContentType(.emailAddress)
                        .autocorrectionDisabled()

                    SecureField("密码", text: $password)
                        .textFieldStyle(.roundedBorder)
                        .textContentType(.newPassword)

                    SecureField("确认密码", text: $confirmPassword)
                        .textFieldStyle(.roundedBorder)
                        .textContentType(.newPassword)

                    if !confirmPassword.isEmpty && !passwordsMatch {
                        Text("两次密码不一致")
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                }
                .padding(.horizontal, 32)

                if let error = authManager.errorMessage {
                    Text(error)
                        .font(.caption)
                        .foregroundStyle(.red)
                        .padding(.horizontal)
                }

                Button {
                    Task {
                        await authManager.register(name: name, email: email, password: password)
                        if authManager.isAuthenticated { dismiss() }
                    }
                } label: {
                    if authManager.isLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text("注册")
                            .frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(.orange)
                .controlSize(.large)
                .padding(.horizontal, 32)
                .disabled(name.isEmpty || email.isEmpty || !passwordsMatch || authManager.isLoading)

                Spacer()
            }
            .padding(.top, 40)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
            }
        }
    }
}
