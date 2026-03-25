import SwiftUI
import StoreKit

struct CreditsShopView: View {
    @Environment(\.dismiss) var dismiss
    @Environment(\.lang) var lang
    @State private var store = StoreKitManager.shared
    @State private var selectedPlan: CreditPlan = allCreditPlans[0]
    @State private var showPlanPicker = false

    var currentProduct: Product? { store.product(for: selectedPlan) }

    var body: some View {
        ZStack(alignment: .topTrailing) {
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    // Header
                    VStack(alignment: .leading, spacing: 8) {
                        Text(lang.t(
                            "プランをアップグレードして\n積分を今すぐ獲得",
                            en: "Upgrade your plan to\nget full credits now",
                            zh: "升级你的计划以\n立即获得全额积分",
                            ko: "플랜을 업그레이드하여\n지금 바로 크레딧 받기"
                        ))
                        .font(.title2).fontWeight(.bold)
                        .lineSpacing(4)
                    }
                    .padding(.top, 56)
                    .padding(.horizontal, 24)
                    .padding(.bottom, 28)

                    // Plan card
                    VStack(alignment: .leading, spacing: 16) {
                        // Plan name + price
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Pro")
                                .font(.headline).fontWeight(.bold)

                            HStack(alignment: .firstTextBaseline, spacing: 2) {
                                if let product = currentProduct {
                                    Text(product.displayPrice)
                                        .font(.system(size: 36, weight: .bold, design: .rounded))
                                } else {
                                    Text("--")
                                        .font(.system(size: 36, weight: .bold, design: .rounded))
                                        .foregroundStyle(.secondary)
                                }
                                Text(lang.t("/ 月", en: "/ mo", zh: "/ 月", ko: "/ 월"))
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                        }

                        // Credits picker button
                        Button {
                            withAnimation(.spring(response: 0.3)) {
                                showPlanPicker.toggle()
                            }
                        } label: {
                            HStack {
                                Text("\(selectedPlan.creditsFormatted) \(lang.t("積分 / 月", en: "credits / mo", zh: "积分 / 月", ko: "크레딧 / 월"))")
                                    .fontWeight(.medium)
                                Spacer()
                                Image(systemName: showPlanPicker ? "chevron.up" : "chevron.down")
                                    .font(.caption)
                            }
                            .foregroundStyle(.primary)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 14)
                            .background(BrandConfig.fieldBackground)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                            .overlay(RoundedRectangle(cornerRadius: 10).stroke(BrandConfig.separator))
                        }

                        // Dropdown list
                        if showPlanPicker {
                            VStack(spacing: 0) {
                                ForEach(allCreditPlans) { plan in
                                    Button {
                                        selectedPlan = plan
                                        withAnimation { showPlanPicker = false }
                                    } label: {
                                        HStack {
                                            Text("\(plan.creditsFormatted) \(lang.t("積分 / 月", en: "credits / mo", zh: "积分 / 月", ko: "크레딧 / 월"))")
                                                .fontWeight(plan.id == selectedPlan.id ? .semibold : .regular)
                                                .foregroundStyle(.primary)
                                            Spacer()
                                            if plan.id == store.activeProductId {
                                                Text(lang.t("現在", en: "Current", zh: "当前", ko: "현재"))
                                                    .font(.caption).foregroundStyle(.secondary)
                                            } else if plan.id == selectedPlan.id {
                                                Image(systemName: "checkmark")
                                                    .font(.caption).foregroundStyle(BrandConfig.brand)
                                            }
                                        }
                                        .padding(.horizontal, 16)
                                        .padding(.vertical, 13)
                                    }
                                    if plan.id != allCreditPlans.last?.id {
                                        Divider().padding(.leading, 16)
                                    }
                                }
                            }
                            .background(BrandConfig.cardBackground)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                            .overlay(RoundedRectangle(cornerRadius: 10).stroke(BrandConfig.separator))
                            .transition(.opacity.combined(with: .scale(scale: 0.97, anchor: .top)))
                        }
                    }
                    .padding(20)
                    .background(BrandConfig.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .shadow(color: .black.opacity(0.05), radius: 8, y: 2)
                    .padding(.horizontal, 16)

                    Spacer(minLength: 32)

                    // Purchase button
                    VStack(spacing: 16) {
                        if let error = store.errorMessage {
                            Text(error)
                                .font(.caption)
                                .foregroundStyle(.red)
                                .multilineTextAlignment(.center)
                        }

                        Button {
                            guard let product = currentProduct else { return }
                            Task { await store.purchase(product) }
                        } label: {
                            ZStack {
                                if store.isPurchasing {
                                    ProgressView().tint(.white)
                                } else {
                                    Text(store.activeProductId == selectedPlan.id
                                         ? lang.t("ダウングレード", en: "Downgrade", zh: "降级", ko: "다운그레이드")
                                         : lang.t("今すぐアップグレード", en: "Upgrade Now", zh: "立即升级", ko: "지금 업그레이드"))
                                        .fontWeight(.semibold)
                                        .foregroundStyle(.white)
                                }
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 16)
                            .background(
                                store.activeProductId == selectedPlan.id
                                ? Color(UIColor.systemGray3)
                                : LinearGradient(colors: [BrandConfig.brand, BrandConfig.brandDeep],
                                                 startPoint: .leading, endPoint: .trailing)
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 14))
                        }
                        .disabled(store.isPurchasing || currentProduct == nil || store.activeProductId == selectedPlan.id)

                        // Auto-renew note
                        Text(lang.t(
                            "毎月自動更新。いつでもキャンセル可能。",
                            en: "Auto-renews monthly. Cancel anytime.",
                            zh: "每月自动续订。随时取消。",
                            ko: "매월 자동 갱신. 언제든지 취소 가능."
                        ))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)

                        // Footer links
                        HStack(spacing: 20) {
                            Link(lang.t("条件", en: "Terms", zh: "条款", ko: "약관"),
                                 destination: URL(string: BrandConfig.termsURL)!)
                            Link(lang.t("プライバシー", en: "Privacy", zh: "隐私", ko: "개인정보"),
                                 destination: URL(string: BrandConfig.privacyURL)!)
                            Button(lang.t("復元", en: "Restore", zh: "恢复", ko: "복원")) {
                                Task { await store.restorePurchases() }
                            }
                        }
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    }
                    .padding(.horizontal, 16)
                    .padding(.bottom, 40)
                }
            }

            // Close button
            Button { dismiss() } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .frame(width: 30, height: 30)
                    .background(BrandConfig.disabledGray)
                    .clipShape(Circle())
            }
            .padding(.top, 16)
            .padding(.trailing, 20)
        }
        .background(BrandConfig.backgroundColor)
        .contentShape(Rectangle())
        .onTapGesture {
            if showPlanPicker {
                withAnimation(.spring(response: 0.3)) { showPlanPicker = false }
            }
        }
        .task {
            if store.products.isEmpty { await store.loadProducts() }
            await store.refreshEntitlements()
            if let active = store.activePlan { selectedPlan = active }
        }
    }
}
