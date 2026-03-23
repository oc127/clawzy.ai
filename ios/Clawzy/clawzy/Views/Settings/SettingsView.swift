import SwiftUI

// MARK: - App Language

enum AppLanguage: String, CaseIterable, Identifiable {
    case japanese = "ja"
    case english  = "en"
    case chinese  = "zh"
    case korean   = "ko"

    var id: String { rawValue }

    var flag: String {
        switch self {
        case .japanese: return "🇯🇵"
        case .english:  return "🇺🇸"
        case .chinese:  return "🇨🇳"
        case .korean:   return "🇰🇷"
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

    var settingsLabel: String {
        switch self {
        case .japanese: return "言語"
        case .english:  return "Language"
        case .chinese:  return "语言"
        case .korean:   return "언어"
        }
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @Environment(AuthManager.self) var authManager
    @AppStorage("appLanguage") private var selectedLanguage: String = AppLanguage.japanese.rawValue

    private var currentLang: AppLanguage {
        AppLanguage(rawValue: selectedLanguage) ?? .japanese
    }

    var body: some View {
        NavigationStack {
            List {
                if let user = authManager.currentUser {
                    // Profile header
                    Section {
                        HStack(spacing: 14) {
                            ZStack {
                                Circle()
                                    .fill(BrandConfig.brand.opacity(0.12))
                                    .frame(width: 54, height: 54)
                                Text(String(user.name.prefix(1)).uppercased())
                                    .font(.title2)
                                    .fontWeight(.bold)
                                    .foregroundStyle(BrandConfig.brand)
                            }
                            VStack(alignment: .leading, spacing: 3) {
                                Text(user.name)
                                    .fontWeight(.semibold)
                                Text(user.email)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .padding(.vertical, 4)
                    }

                    // Credits
                    Section("クレジット") {
                        HStack {
                            Label("残高", systemImage: "bolt.fill")
                            Spacer()
                            Text("\(user.creditBalance)")
                                .fontWeight(.bold)
                                .foregroundStyle(BrandConfig.brand)
                        }
                    }
                }

                // Language
                Section(currentLang.settingsLabel) {
                    ForEach(AppLanguage.allCases) { lang in
                        Button {
                            selectedLanguage = lang.rawValue
                        } label: {
                            HStack(spacing: 12) {
                                Text(lang.flag)
                                    .font(.title3)
                                Text(lang.localName)
                                    .foregroundStyle(.primary)
                                Spacer()
                                if selectedLanguage == lang.rawValue {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundStyle(BrandConfig.brand)
                                }
                            }
                        }
                    }
                }

                // About
                Section("このアプリについて") {
                    HStack {
                        Label("バージョン", systemImage: "info.circle")
                        Spacer()
                        Text("1.0.0")
                            .foregroundStyle(.secondary)
                    }

                    Link(destination: URL(string: BrandConfig.privacyURL)!) {
                        Label("\(BrandConfig.appName) を開く", systemImage: "safari")
                            .foregroundStyle(BrandConfig.brand)
                    }

                    Link(destination: URL(string: BrandConfig.termsURL)!) {
                        Label("利用規約", systemImage: "doc.text")
                            .foregroundStyle(BrandConfig.brand)
                    }
                }

                // Logout
                Section {
                    Button(role: .destructive) {
                        authManager.logout()
                    } label: {
                        HStack {
                            Spacer()
                            Label("ログアウト", systemImage: "rectangle.portrait.and.arrow.right")
                            Spacer()
                        }
                    }
                }
            }
            .navigationTitle("設定")
        }
    }
}
