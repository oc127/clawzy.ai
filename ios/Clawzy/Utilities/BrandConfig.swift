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
    /// Japan crimson — #ED1A3A  (primary brand red)
    static let brand          = Color(red: 0.93, green: 0.10, blue: 0.23)
    static let brandDeep      = Color(red: 0.78, green: 0.04, blue: 0.17)
    static let primaryColor   = brand
    static let accentColor    = brand

    /// Adaptive background colors — auto-switch light ↔ dark mode
    static let backgroundColor = Color(UIColor.systemGroupedBackground)
    static let cardBackground  = Color(UIColor.secondarySystemBackground)
    static let fieldBackground = Color(UIColor.tertiarySystemBackground)
    static let separator       = Color(UIColor.separator)
    static let disabledGray    = Color(UIColor.systemGray4)

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
        ZStack {
            RoundedRectangle(cornerRadius: size * 0.22)
                .fill(
                    LinearGradient(
                        colors: [BrandConfig.brand, BrandConfig.brandDeep],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: size, height: size)
            Text("N")
                .font(.system(size: size * 0.48, weight: .bold, design: .rounded))
                .foregroundStyle(.white)
        }
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
