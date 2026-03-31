import Foundation
import Observation

// MARK: - Models (shared between Market and InstalledPluginsView)

struct InstalledPlugin: Identifiable, Decodable {
    var id: String { slug }
    let slug: String
    let version: String?
    let name: String?
}

struct PluginsListResponse: Decodable {
    let plugins: [InstalledPlugin]
}

// MARK: - Shared store

@Observable
final class PluginsStore {
    private(set) var pluginsByAgent: [String: [InstalledPlugin]] = [:]
    private var loadingSet: Set<String> = []
    private(set) var errorByAgent: [String: String] = [:]

    func isLoading(agentId: String) -> Bool { loadingSet.contains(agentId) }

    func plugins(for agentId: String) -> [InstalledPlugin] {
        pluginsByAgent[agentId] ?? []
    }

    func fetch(agentId: String) async {
        loadingSet.insert(agentId)
        errorByAgent.removeValue(forKey: agentId)
        defer { loadingSet.remove(agentId) }
        do {
            let resp: PluginsListResponse = try await APIClient.shared.request(
                Constants.API.agentPlugins(agentId)
            )
            pluginsByAgent[agentId] = resp.plugins
        } catch {
            errorByAgent[agentId] = error.localizedDescription
        }
    }

    func uninstall(slug: String, agentId: String) async throws {
        try await APIClient.shared.requestVoid(
            Constants.API.agentPlugin(agentId, slug: slug),
            method: "DELETE"
        )
        pluginsByAgent[agentId]?.removeAll { $0.slug == slug }
    }
}
