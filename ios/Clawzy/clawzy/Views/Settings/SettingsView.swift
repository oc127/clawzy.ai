import SwiftUI

struct SettingsView: View {
    @Environment(AuthManager.self) var authManager

    var body: some View {
        NavigationStack {
            List {
                // 用户信息
                if let user = authManager.currentUser {
                    Section("账户") {
                        HStack {
                            // 头像
                            ZStack {
                                Circle()
                                    .fill(.orange.opacity(0.2))
                                    .frame(width: 50, height: 50)
                                Text(String(user.name.prefix(1)).uppercased())
                                    .font(.title2)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.orange)
                            }

                            VStack(alignment: .leading, spacing: 4) {
                                Text(user.name)
                                    .fontWeight(.medium)
                                Text(user.email)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            .padding(.leading, 8)
                        }
                        .padding(.vertical, 4)

                        HStack {
                            Text("积分余额")
                            Spacer()
                            Text("\(user.creditBalance)")
                                .fontWeight(.bold)
                                .foregroundStyle(.orange)
                        }
                    }
                }

                // 关于
                Section("关于") {
                    HStack {
                        Text("版本")
                        Spacer()
                        Text("1.0.0")
                            .foregroundStyle(.secondary)
                    }

                    Link("访问 \(BrandConfig.appName)", destination: URL(string: BrandConfig.privacyURL)!)
                }

                // 登出
                Section {
                    Button(role: .destructive) {
                        authManager.logout()
                    } label: {
                        HStack {
                            Spacer()
                            Text("退出登录")
                            Spacer()
                        }
                    }
                }
            }
            .navigationTitle("设置")
        }
    }
}
