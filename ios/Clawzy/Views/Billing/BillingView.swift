import SwiftUI

@MainActor
final class BillingViewModel: ObservableObject {
    @Published var credits: CreditsInfo?
    @Published var plans: [PlanInfo] = []
    @Published var isLoading = false

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            async let c: CreditsInfo = APIClient.shared.request(path: "/billing/credits")
            async let p: [PlanInfo] = APIClient.shared.request(path: "/billing/plans")
            credits = try await c
            plans = try await p
        } catch {
            // Silently fail — user sees empty state
        }
    }
}

struct BillingView: View {
    @StateObject private var vm = BillingViewModel()

    var body: some View {
        NavigationStack {
            List {
                if let credits = vm.credits {
                    Section("Your Credits") {
                        LabeledContent("Balance", value: "\(credits.balance)")
                        LabeledContent("Used This Period", value: "\(credits.used_this_period)")
                        LabeledContent("Current Plan", value: credits.plan.capitalized)
                    }
                }

                Section("Available Plans") {
                    ForEach(vm.plans) { plan in
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text(plan.name)
                                    .font(.headline)
                                Spacer()
                                Text("$\(Int(plan.price_monthly))/mo")
                                    .foregroundStyle(.secondary)
                            }
                            Text("\(plan.credits_included) credits · \(plan.max_agents) agent\(plan.max_agents == 1 ? "" : "s")")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
            .navigationTitle("Billing")
            .refreshable {
                await vm.load()
            }
            .overlay {
                if vm.isLoading && vm.credits == nil {
                    ProgressView()
                }
            }
            .task {
                await vm.load()
            }
        }
    }
}
