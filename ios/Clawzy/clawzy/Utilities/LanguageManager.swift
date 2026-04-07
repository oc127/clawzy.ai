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

    /// Translate skill store category tab labels (keyed by SkillCategory rawValue).
    func skillCategoryLabel(_ rawValue: String) -> String {
        switch rawValue {
        case "featured":     return t("おすすめ",        en: "Featured",     zh: "精选",    ko: "추천")
        case "nipponclaw":   return "NipponClaw"
        case "japan":        return t("日本",            en: "Japan",        zh: "日本",    ko: "일본")
        case "business":     return t("ビジネス",        en: "Business",     zh: "商务",    ko: "비즈니스")
        case "writing":      return t("ライティング",    en: "Writing",      zh: "写作",    ko: "라이팅")
        case "marketing":    return t("マーケティング",  en: "Marketing",    zh: "营销",    ko: "마케팅")
        case "education":    return t("教育",            en: "Education",    zh: "教育",    ko: "교육")
        case "design":       return t("デザイン",        en: "Design",       zh: "设计",    ko: "디자인")
        case "development":  return t("開発",            en: "Development",  zh: "开发",    ko: "개발")
        case "finance":      return t("ファイナンス",    en: "Finance",      zh: "财务",    ko: "파이낸스")
        case "lifestyle":    return t("生活",            en: "Lifestyle",    zh: "生活",    ko: "라이프스타일")
        default:             return rawValue
        }
    }
}

// Convenience environment key
private struct LanguageManagerKey: EnvironmentKey {
    static let defaultValue = LanguageManager()
}

private struct TabBarVisibleKey: EnvironmentKey {
    static let defaultValue: Binding<Bool> = .constant(true)
}

extension EnvironmentValues {
    var lang: LanguageManager {
        get { self[LanguageManagerKey.self] }
        set { self[LanguageManagerKey.self] = newValue }
    }

    var tabBarVisible: Binding<Bool> {
        get { self[TabBarVisibleKey.self] }
        set { self[TabBarVisibleKey.self] = newValue }
    }
}
