import SwiftUI

/// All brand-specific values are defined here.
/// When adding a new market, create a new Xcode target and override these values
/// using a target-specific BrandConfig.swift (exclude this file from that target).
struct BrandConfig {
    // MARK: - Identity
    static let appName        = "NipponClaw"
    static let bundleID       = "ai.clawzy.nipponclaw"
    static let marketRegion   = "JP"

    // MARK: - Colors
    /// NipponClaw brand red — #E53935
    static let brand          = Color(red: 0.898, green: 0.224, blue: 0.208)
    static let brandDeep      = Color(red: 0.776, green: 0.157, blue: 0.157)
    static let primaryColor   = brand
    static let accentColor    = brand

    /// Adaptive background colors — auto-switch light ↔ dark mode
    static let backgroundColor = Color(UIColor.systemGroupedBackground)
    static let cardBackground  = Color(UIColor.secondarySystemBackground)
    static let fieldBackground = Color(UIColor.tertiarySystemBackground)
    static let separator       = Color(UIColor.separator)
    static let disabledGray    = Color(UIColor.systemGray4)

    // Adaptive surface colors — follow system light/dark mode
    static let darkBg        = Color(UIColor.systemGroupedBackground)
    static let darkSurface   = Color(UIColor.secondarySystemGroupedBackground)
    static let darkCard      = Color(UIColor.secondarySystemBackground)
    static let darkSeparator = Color(UIColor.separator)

    // MARK: - Design System Tokens (adaptive light/dark)

    /// Page background — pure black dark / white light
    static let background      = Color(UIColor.systemBackground)
    /// Standard card surface — #1C1C1E dark / #F5F5F5 light
    static let surface         = Color(UIColor { tc in
        tc.userInterfaceStyle == .dark
            ? UIColor(red: 0.110, green: 0.110, blue: 0.118, alpha: 1)
            : UIColor(red: 0.961, green: 0.961, blue: 0.961, alpha: 1)
    })
    /// Elevated card surface — #2C2C2E dark / white light
    static let surfaceElevated = Color(UIColor { tc in
        tc.userInterfaceStyle == .dark
            ? UIColor(red: 0.173, green: 0.173, blue: 0.180, alpha: 1)
            : UIColor.white
    })
    static let textSecondary   = Color(UIColor.secondaryLabel)
    static let textTertiary    = Color(UIColor.tertiaryLabel)

    // MARK: - Spacing

    enum Spacing {
        static let xs: CGFloat  = 4
        static let sm: CGFloat  = 8
        static let md: CGFloat  = 12
        static let lg: CGFloat  = 16
        static let xl: CGFloat  = 24
        static let xxl: CGFloat = 32
    }

    // MARK: - Radius

    enum Radius {
        static let card: CGFloat   = 16
        static let chip: CGFloat   = 20
        static let button: CGFloat = 12
    }

    // MARK: - Strings
    static let tagline        = "AI Agents, Unleashed"
    static let taglineJP      = "AIエージェントを、自由に。"

    // MARK: - App Store
    static let appStoreID     = ""   // fill after App Store Connect submission
    static let privacyURL     = "https://nipponclaw.com/privacy"
    static let termsURL       = "https://nipponclaw.com/terms"
}

// MARK: - Shared brand components

struct NipponLogo: View {
    var size: CGFloat = 44

    var body: some View {
        Image("ClawzyLogo")
            .resizable()
            .scaledToFit()
            .frame(width: size, height: size)
            .clipShape(RoundedRectangle(cornerRadius: size * 0.22))
    }
}

struct BrandButton: View {
    let title: String
    let isLoading: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            ZStack {
                if isLoading {
                    ProgressView().tint(.white)
                } else {
                    Text(title)
                        .fontWeight(.semibold)
                        .foregroundStyle(.white)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 15)
            .background(
                LinearGradient(
                    colors: [BrandConfig.brand, BrandConfig.brandDeep],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
    }
}

struct LabeledField<Content: View>: View {
    let label: String
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label)
                .font(.footnote)
                .fontWeight(.medium)
                .foregroundStyle(.secondary)
            content()
                .padding(.horizontal, 14)
                .padding(.vertical, 12)
                .background(BrandConfig.fieldBackground)
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(BrandConfig.separator, lineWidth: 1)
                )
        }
    }
}
