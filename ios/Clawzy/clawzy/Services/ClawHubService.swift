import Foundation
import Observation

// MARK: - Models

struct ClawHubPlugin: Identifiable, Decodable {
    var id: String { slug }
    let slug: String
    let name: String
    let description: String?
    let author: String?
    let downloads: Int?
    let version: String?
    let tags: [String]?
}

struct ClawHubSearchResponse: Decodable {
    let items: [ClawHubPlugin]
    let total: Int
}

struct ClawHubInstallResponse: Decodable {
    let success: Bool
    let output: String?
}

private struct ClawHubInstallRequest: Encodable {
    let agentId: String
    let slug: String
    let version: String

    enum CodingKeys: String, CodingKey {
        case agentId = "agent_id"
        case slug
        case version
    }
}

// MARK: - Service

@Observable
final class ClawHubService {
    var plugins: [ClawHubPlugin] = []
    var isLoading = false
    var errorMessage: String?
    var totalCount = 0

    private let api = APIClient.shared

    /// Search plugins. Pass `page > 1` to append results.
    func search(query: String = "", page: Int = 1) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        var components = URLComponents()
        components.queryItems = [
            URLQueryItem(name: "q", value: query),
            URLQueryItem(name: "page", value: "\(page)"),
            URLQueryItem(name: "limit", value: "20"),
        ]
        let qs = components.percentEncodedQuery.map { "?\($0)" } ?? ""
        let path = Constants.API.clawHubSearch + qs

        do {
            let response: ClawHubSearchResponse = try await api.request(path)
            if page == 1 {
                plugins = response.items
            } else {
                plugins += response.items
            }
            totalCount = response.total
        } catch {
            errorMessage = error.localizedDescription
            if page == 1 { plugins = [] }
        }
    }

    /// Install a plugin into an agent's container.
    func install(agentId: String, slug: String, version: String = "latest") async throws {
        let body = ClawHubInstallRequest(agentId: agentId, slug: slug, version: version)
        let _: ClawHubInstallResponse = try await api.request(
            Constants.API.clawHubInstall,
            method: "POST",
            body: body
        )
    }
}
