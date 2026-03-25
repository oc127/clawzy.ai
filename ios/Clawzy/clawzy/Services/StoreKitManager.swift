import StoreKit

// MARK: - Credit plan definition

struct CreditPlan: Identifiable {
    let id: String          // matches App Store Connect product ID
    let credits: Int
    let usdEquivalent: Int  // display only

    var creditsFormatted: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        return formatter.string(from: NSNumber(value: credits)) ?? "\(credits)"
    }
}

let allCreditPlans: [CreditPlan] = [
    CreditPlan(id: "ai.clawzy.app.sub.4k",    credits:   4_000, usdEquivalent:   20),
    CreditPlan(id: "ai.clawzy.app.sub.8k",    credits:   8_000, usdEquivalent:   40),
    CreditPlan(id: "ai.clawzy.app.sub.12k",   credits:  12_000, usdEquivalent:   60),
    CreditPlan(id: "ai.clawzy.app.sub.16k",   credits:  16_000, usdEquivalent:   80),
    CreditPlan(id: "ai.clawzy.app.sub.20k",   credits:  20_000, usdEquivalent:  100),
    CreditPlan(id: "ai.clawzy.app.sub.40k",   credits:  40_000, usdEquivalent:  200),
    CreditPlan(id: "ai.clawzy.app.sub.63k",   credits:  63_000, usdEquivalent:  300),
    CreditPlan(id: "ai.clawzy.app.sub.85k",   credits:  85_000, usdEquivalent:  400),
    CreditPlan(id: "ai.clawzy.app.sub.110k",  credits: 110_000, usdEquivalent:  500),
    CreditPlan(id: "ai.clawzy.app.sub.170k",  credits: 170_000, usdEquivalent:  749),
    CreditPlan(id: "ai.clawzy.app.sub.230k",  credits: 230_000, usdEquivalent: 1000),
]

// MARK: - StoreKit manager

@MainActor
@Observable
final class StoreKitManager {
    static let shared = StoreKitManager()

    var products: [Product] = []
    var activeProductId: String? = nil
    var isPurchasing = false
    var errorMessage: String?

    nonisolated(unsafe) private var updateTask: Task<Void, Never>?

    init() {
        updateTask = Task { await listenForTransactions() }
        Task { await loadProducts() }
    }

    private static func localizedString(ja: String, en: String, zh: String, ko: String) -> String {
        let code = Locale.current.language.languageCode?.identifier ?? "en"
        switch code {
        case "ja": return ja
        case "zh": return zh
        case "ko": return ko
        default:   return en
        }
    }

    deinit { updateTask?.cancel() }

    // MARK: - Load products from App Store

    func loadProducts() async {
        let ids = Set(allCreditPlans.map(\.id))
        do {
            let fetched = try await Product.products(for: ids)
            products = fetched.sorted { $0.price < $1.price }
        } catch {
            errorMessage = Self.localizedString(
                ja: "商品の読み込みに失敗しました",
                en: "Failed to load products",
                zh: "加载商品失败",
                ko: "상품 로드 실패"
            )
        }
    }

    // MARK: - Purchase

    func purchase(_ product: Product) async {
        guard activeProductId != product.id else { return }
        isPurchasing = true
        errorMessage = nil
        defer { isPurchasing = false }
        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                let tx = try checkVerified(verification)
                await refreshEntitlements()
                await tx.finish()
            case .pending, .userCancelled:
                break
            @unknown default:
                break
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Restore

    func restorePurchases() async {
        try? await AppStore.sync()
        await refreshEntitlements()
    }

    // MARK: - Entitlements

    func refreshEntitlements() async {
        for await result in Transaction.currentEntitlements {
            if let tx = try? checkVerified(result),
               tx.productType == .autoRenewable {
                activeProductId = tx.productID
                return
            }
        }
        activeProductId = nil
    }

    // MARK: - Transaction listener

    private func listenForTransactions() async {
        for await result in Transaction.updates {
            if let tx = try? checkVerified(result) {
                await refreshEntitlements()
                await tx.finish()
            }
        }
    }

    // MARK: - Helper

    private func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified(_, let error): throw error
        case .verified(let value): return value
        }
    }

    // MARK: - Convenience

    func product(for plan: CreditPlan) -> Product? {
        products.first { $0.id == plan.id }
    }

    var activePlan: CreditPlan? {
        guard let id = activeProductId else { return nil }
        return allCreditPlans.first { $0.id == id }
    }
}
