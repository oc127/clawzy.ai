import SwiftUI

struct LoginView: View {
    @Environment(AuthManager.self) var authManager
    @State private var email = ""
    @State private var password = ""
    @State private var showRegister = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 32) {
                Spacer()

                // Logo 区域
                VStack(spacing: 8) {
                    Text("🦞")
                        .font(.system(size: 64))
                    Text(BrandConfig.appName)
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    Text(BrandConfig.tagline)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                // 输入表单
                VStack(spacing: 16) {
                    TextField("邮箱", text: $email)
                        .textFieldStyle(.roundedBorder)
                        .textContentType(.emailAddress)
                        .autocorrectionDisabled()

                    SecureField("密码", text: $password)
                        .textFieldStyle(.roundedBorder)
                        .textContentType(.password)
                }
                .padding(.horizontal, 32)

                // 错误提示
                if let error = authManager.errorMessage {
                    Text(error)
                        .font(.caption)
                        .foregroundStyle(.red)
                        .padding(.horizontal)
                }

                // 登录按钮
                Button {
                    Task { await authManager.login(email: email, password: password) }
                } label: {
                    if authManager.isLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text("登录")
                            .frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(.orange)
                .controlSize(.large)
                .padding(.horizontal, 32)
                .disabled(email.isEmpty || password.isEmpty || authManager.isLoading)

                // 注册入口
                Button("没有账号？注册") {
                    showRegister = true
                }
                .foregroundStyle(.orange)

                Spacer()
            }
            .sheet(isPresented: $showRegister) {
                RegisterView()
            }
        }
    }
}
