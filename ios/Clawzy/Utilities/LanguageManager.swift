import SwiftUI

@Observable
final class LanguageManager {
    var current: String {
        didSet { UserDefaults.standard.set(current, forKey: "appLanguage") }
    }

    init() {
        if let saved = UserDefaults.standard.string(forKey: "appLanguage") {
            self.current = saved
        } else {
            // No explicit preference — follow system locale
            let systemLang = Locale.preferredLanguages.first ?? "en"
            if systemLang.hasPrefix("ja") { self.current = "ja" }
            else if systemLang.hasPrefix("zh") { self.current = "zh" }
            else if systemLang.hasPrefix("ko") { self.current = "ko" }
            else { self.current = "en" }
        }
    }

    /// Return the string for the active language.
    func t(_ ja: String, en: String = "", zh: String = "", ko: String = "") -> String {
        switch current {
        case "en": return en.isEmpty ? ja : en
        case "zh": return zh.isEmpty ? ja : zh
        case "ko": return ko.isEmpty ? ja : ko
        default:   return ja
        }
    }

    /// Translate known template category names.
    func categoryLabel(_ ja: String) -> String {
        switch ja {
        case "ビジネス": return t(ja, en: "Business",  zh: "商务",  ko: "비즈니스")
        case "教育":    return t(ja, en: "Education",  zh: "教育",  ko: "교육")
        case "創作":    return t(ja, en: "Creative",   zh: "创作",  ko: "창작")
        case "分析":    return t(ja, en: "Analysis",   zh: "分析",  ko: "분석")
        case "コード":  return t(ja, en: "Code",       zh: "编程",  ko: "코드")
        default:        return ja
        }
    }
}

// Convenience environment key
private struct LanguageManagerKey: EnvironmentKey {
    static let defaultValue = LanguageManager()
}

extension EnvironmentValues {
    var lang: LanguageManager {
        get { self[LanguageManagerKey.self] }
        set { self[LanguageManagerKey.self] = newValue }
    }
}
