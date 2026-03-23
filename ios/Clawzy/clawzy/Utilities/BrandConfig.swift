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
    static let primaryColor   = Color(red: 0.737, green: 0.0, blue: 0.176)  // Japanese red #BC002D
    static let accentColor    = Color(red: 0.0, green: 0.4, blue: 1.0)      // Electric blue #0066FF
    static let backgroundColor = Color.white

    // MARK: - Strings
    static let tagline        = "AI Agents, Unleashed"
    static let taglineJP      = "AIエージェントを、自由に。"

    // MARK: - App Store
    static let appStoreID     = ""   // fill after App Store Connect submission
    static let privacyURL     = "https://clawzy.ai/privacy"
    static let termsURL       = "https://clawzy.ai/terms"
}
