import Foundation
import Observation

/// Overall service health status
enum ServiceStatus {
    case online   // backend + openclaw both up
    case degraded // backend up, openclaw down
    case offline  // backend unreachable
}

/// Periodically pings /health and exposes reactive state.
/// Retries with exponential back-off (max 3 attempts) on failure.
@Observable
final class HealthMonitor {
    var isBackendOnline = false
    var isOpenClawOnline = false
    var lastChecked: Date?
    var errorMessage: String?
    var isChecking = false

    var overallStatus: ServiceStatus {
        if !isBackendOnline { return .offline }
        if !isOpenClawOnline { return .degraded }
        return .online
    }

    private var monitorTask: Task<Void, Never>?
    private let checkInterval: TimeInterval = 30
    private let maxRetries = 3

    // MARK: - Lifecycle

    func startMonitoring() {
        monitorTask?.cancel()
        monitorTask = Task { [weak self] in
            while !Task.isCancelled {
                await self?.performCheck(retryCount: 0)
                try? await Task.sleep(for: .seconds(self?.checkInterval ?? 30))
            }
        }
    }

    func stopMonitoring() {
        monitorTask?.cancel()
        monitorTask = nil
    }

    /// One-shot check used at app startup (awaitable).
    func checkHealth() async {
        await MainActor.run { isChecking = true }
        defer { Task { @MainActor in self.isChecking = false } }
        await performCheck(retryCount: 0)
    }

    // MARK: - Internal

    private func performCheck(retryCount: Int) async {
        guard let url = URL(string: Constants.baseURL + "/health") else { return }
        var req = URLRequest(url: url)
        req.timeoutInterval = 5

        do {
            let (data, response) = try await URLSession.shared.data(for: req)
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            let backendOk = (200...299).contains(code)

            var openclawOk = false
            if backendOk,
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                openclawOk = (json["openclaw"] as? String) == "ok"
            }

            await MainActor.run {
                self.isBackendOnline = backendOk
                self.isOpenClawOnline = openclawOk
                self.lastChecked = Date()
                self.errorMessage = nil
            }
        } catch {
            if retryCount < maxRetries {
                let delay = pow(2.0, Double(retryCount))
                try? await Task.sleep(for: .seconds(delay))
                await performCheck(retryCount: retryCount + 1)
            } else {
                await MainActor.run {
                    self.isBackendOnline = false
                    self.isOpenClawOnline = false
                    self.errorMessage = error.localizedDescription
                }
            }
        }
    }
}
