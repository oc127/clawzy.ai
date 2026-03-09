import Foundation

/// Lightweight REST client mirroring the web `api.ts`.
/// Handles Bearer auth, 401 auto-refresh, and JSON encoding/decoding.
final class APIClient: @unchecked Sendable {
    static let shared = APIClient()

    private let session = URLSession.shared
    private let baseURL = Configuration.apiBaseURL
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()

    // MARK: - Generic request

    /// Perform an authenticated (by default) JSON request.
    func request<T: Decodable>(
        path: String,
        method: String = "GET",
        body: (any Encodable)? = nil,
        authenticated: Bool = true
    ) async throws -> T {
        let data = try await rawRequest(path: path, method: method, body: body, authenticated: authenticated)
        return try decoder.decode(T.self, from: data)
    }

    /// Fire-and-forget variant for endpoints that return 204.
    func requestVoid(
        path: String,
        method: String = "GET",
        body: (any Encodable)? = nil,
        authenticated: Bool = true
    ) async throws {
        _ = try await rawRequest(path: path, method: method, body: body, authenticated: authenticated)
    }

    // MARK: - Internal

    private func rawRequest(
        path: String,
        method: String,
        body: (any Encodable)?,
        authenticated: Bool
    ) async throws -> Data {
        var urlRequest = URLRequest(url: URL(string: "\(baseURL)\(path)")!)
        urlRequest.httpMethod = method
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if authenticated, let token = await AuthService.shared.accessToken {
            urlRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body {
            urlRequest.httpBody = try encoder.encode(AnyEncodable(body))
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let http = response as? HTTPURLResponse else {
            throw APIError.unknown
        }

        // 401 → try refresh once, then retry
        if http.statusCode == 401 && authenticated {
            let refreshed = await AuthService.shared.tryRefresh()
            if refreshed {
                // Rebuild with new token
                if let newToken = await AuthService.shared.accessToken {
                    urlRequest.setValue("Bearer \(newToken)", forHTTPHeaderField: "Authorization")
                }
                let (retryData, retryRes) = try await session.data(for: urlRequest)
                guard let retryHttp = retryRes as? HTTPURLResponse else { throw APIError.unknown }
                if retryHttp.statusCode >= 400 {
                    throw APIError.http(status: retryHttp.statusCode, detail: String(data: retryData, encoding: .utf8))
                }
                return retryData
            } else {
                await AuthService.shared.clearTokens()
                throw APIError.unauthorized
            }
        }

        if http.statusCode == 204 {
            return Data()
        }

        if http.statusCode >= 400 {
            // Try to extract `detail` from JSON body
            if let errBody = try? JSONDecoder().decode(ErrorBody.self, from: data) {
                throw APIError.http(status: http.statusCode, detail: errBody.detail)
            }
            throw APIError.http(status: http.statusCode, detail: String(data: data, encoding: .utf8))
        }

        return data
    }
}

// MARK: - Error types

enum APIError: LocalizedError {
    case unauthorized
    case http(status: Int, detail: String?)
    case unknown

    var errorDescription: String? {
        switch self {
        case .unauthorized:
            return "Session expired. Please log in again."
        case .http(_, let detail):
            return detail ?? "Request failed."
        case .unknown:
            return "An unknown error occurred."
        }
    }
}

private struct ErrorBody: Codable {
    let detail: String
}

// MARK: - Type-erased Encodable wrapper

private struct AnyEncodable: Encodable {
    private let _encode: (Encoder) throws -> Void

    init(_ value: any Encodable) {
        _encode = { encoder in try value.encode(to: encoder) }
    }

    func encode(to encoder: Encoder) throws {
        try _encode(encoder)
    }
}
