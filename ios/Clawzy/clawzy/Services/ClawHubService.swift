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

// Minimal shape of the skill detail endpoint response
private struct SkillDetailEnvelope: Decodable {
    struct SkillInfo: Decodable {
        let slug: String?
        let name: String?
        let displayName: String?
        let description: String?
        struct Stats: Decodable { let downloads: Int? }
        let stats: Stats?
    }
    struct Owner: Decodable {
        let handle: String?
        let displayName: String?
    }
    struct LatestVersion: Decodable { let version: String? }

    let skill: SkillInfo?
    let owner: Owner?
    let latestVersion: LatestVersion?
    // Fallback flat fields
    let slug: String?
    let name: String?
    let description: String?
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
    func search(query: String = "", page: Int = 1, limit: Int = 20, lang: String = "ja") async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        guard let items = await fetchRaw(query: query, page: page, limit: limit, lang: lang) else { return }
        if page == 1 {
            plugins = items
        } else {
            plugins += items
        }
    }

    /// Fetch a curated list of skills by slug (for NipponClaw section).
    func fetchCurated(slugs: [String]) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        var results: [ClawHubPlugin] = []
        await withTaskGroup(of: ClawHubPlugin?.self) { group in
            for slug in slugs {
                group.addTask { [weak self] in
                    guard let self else { return nil }
                    return await self.fetchSkillBySlug(slug)
                }
            }
            for await result in group {
                if let p = result { results.append(p) }
            }
        }

        // Preserve the original curated order
        let orderMap = Dictionary(uniqueKeysWithValues: slugs.enumerated().map { ($1, $0) })
        plugins = results.sorted { (orderMap[$0.slug] ?? 99) < (orderMap[$1.slug] ?? 99) }

        if plugins.isEmpty {
            errorMessage = "No skills found"
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

    // MARK: - Private

    private func fetchSkillBySlug(_ slug: String) async -> ClawHubPlugin? {
        let path = Constants.API.clawHubSkill(slug)
        guard let env: SkillDetailEnvelope = try? await api.request(path) else { return nil }
        let info = env.skill
        let displayName = info?.displayName
            ?? info?.name
            ?? env.name
            ?? slug.replacingOccurrences(of: "-", with: " ").capitalized
        return ClawHubPlugin(
            slug: slug,
            name: displayName,
            description: info?.description ?? env.description,
            author: env.owner?.handle ?? env.owner?.displayName,
            downloads: info?.stats?.downloads,
            version: env.latestVersion?.version,
            tags: nil
        )
    }

    private func fetchRaw(query: String = "", page: Int = 1, limit: Int = 20, lang: String = "ja") async -> [ClawHubPlugin]? {
        var components = URLComponents()
        components.queryItems = [
            URLQueryItem(name: "q", value: query),
            URLQueryItem(name: "page", value: "\(page)"),
            URLQueryItem(name: "limit", value: "\(limit)"),
            URLQueryItem(name: "lang", value: lang),
        ]
        let qs = components.percentEncodedQuery.map { "?\($0)" } ?? ""
        let path = Constants.API.clawHubSearch + qs

        do {
            let response: ClawHubSearchResponse = try await api.request(path)
            totalCount = response.total
            return response.items
        } catch {
            errorMessage = error.localizedDescription
            return nil
        }
    }
}
