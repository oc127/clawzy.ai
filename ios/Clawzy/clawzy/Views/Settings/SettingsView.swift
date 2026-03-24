import SwiftUI

// MARK: - App Language

enum AppLanguage: String, CaseIterable, Identifiable {
    case japanese = "ja"
    case english  = "en"
    case chinese  = "zh"
    case korean   = "ko"

    var id: String { rawValue }

    var badge: String {
        switch self {
        case .japanese: return "JP"
        case .english:  return "EN"
        case .chinese:  return "ZH"
        case .korean:   return "KR"
        }
    }

    var localName: String {
        switch self {
        case .japanese: return "日本語"
        case .english:  return "English"
        case .chinese:  return "中文"
        case .korean:   return "한국어"
        }
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @Environment(AuthManager.self) var authManager
    @Environment(\.lang) var lang
    @AppStorage("appColorScheme") private var colorScheme: String = "system"

    var body: some View {
        NavigationStack {
            List {
                if let user = authManager.currentUser {
                    Section {
                        HStack(spacing: 14) {
                            ZStack {
                                Circle()
                                    .fill(BrandConfig.brand.opacity(0.12))
                                    .frame(width: 54, height: 54)
                                Text(String(user.name.prefix(1)).uppercased())
                                    .font(.title2).fontWeight(.bold)
                                    .foregroundStyle(BrandConfig.brand)
                            }
                            VStack(alignment: .leading, spacing: 3) {
                                Text(user.name).fontWeight(.semibold)
                                Text(user.email).font(.caption).foregroundStyle(.secondary)
                            }
                        }
                        .padding(.vertical, 4)
                    }

                    Section(lang.t("クレジット", en: "Credits", zh: "点数", ko: "크레딧")) {
                        HStack {
                            Label(lang.t("残高", en: "Balance", zh: "余额", ko: "잔액"),
                                  systemImage: "bolt.fill")
                            Spacer()
                            Text("\(user.creditBalance)")
                                .fontWeight(.bold)
                                .foregroundStyle(BrandConfig.brand)
                        }
                    }
                }

                Section(lang.t("外観", en: "Appearance", zh: "外观", ko: "외관")) {
                    HStack {
                        Label(lang.t("テーマ", en: "Theme", zh: "主题", ko: "테마"),
                              systemImage: "circle.lefthalf.filled")
                        Spacer()
                        Picker("", selection: $colorScheme) {
                            Text(lang.t("自動", en: "Auto", zh: "自动", ko: "자동")).tag("system")
                            Image(systemName: "sun.max.fill").tag("light")
                            Image(systemName: "moon.fill").tag("dark")
                        }
                        .pickerStyle(.segmented)
                        .frame(width: 120)
                    }
                }

                Section(lang.t("言語", en: "Language", zh: "语言", ko: "언어")) {
                    Picker(selection: Binding(
                        get: { lang.current },
                        set: { lang.current = $0 }
                    )) {
                        ForEach(AppLanguage.allCases) { language in
                            HStack {
                                Text(language.badge)
                                    .font(.caption.bold())
                                    .foregroundStyle(BrandConfig.brand)
                                    .frame(width: 28, height: 20)
                                    .background(BrandConfig.brand.opacity(0.10))
                                    .clipShape(RoundedRectangle(cornerRadius: 4))
                                Text(language.localName)
                            }
                            .tag(language.rawValue)
                        }
                    } label: {
                        Label(
                            AppLanguage(rawValue: lang.current)?.localName ?? "日本語",
                            systemImage: "globe"
                        )
                    }
                    .pickerStyle(.navigationLink)
                }

                Section(lang.t("このアプリについて", en: "About", zh: "关于", ko: "앱 정보")) {
                    HStack {
                        Label(lang.t("バージョン", en: "Version", zh: "版本", ko: "버전"),
                              systemImage: "info.circle")
                        Spacer()
                        Text("1.0.0").foregroundStyle(.secondary)
                    }
                    Link(destination: URL(string: BrandConfig.privacyURL)!) {
                        Label("\(BrandConfig.appName) を開く", systemImage: "safari")
                            .foregroundStyle(BrandConfig.brand)
                    }
                    Link(destination: URL(string: BrandConfig.termsURL)!) {
                        Label(lang.t("利用規約", en: "Terms", zh: "使用条款", ko: "이용약관"),
                              systemImage: "doc.text")
                        .foregroundStyle(BrandConfig.brand)
                    }
                }

                Section {
                    Button(role: .destructive) {
                        authManager.logout()
                    } label: {
                        HStack {
                            Spacer()
                            Label(lang.t("ログアウト", en: "Logout", zh: "退出登录", ko: "로그아웃"),
                                  systemImage: "rectangle.portrait.and.arrow.right")
                            Spacer()
                        }
                    }
                }
            }
            .navigationTitle(lang.t("設定", en: "Settings", zh: "设置", ko: "설정"))
        }
    }
}
