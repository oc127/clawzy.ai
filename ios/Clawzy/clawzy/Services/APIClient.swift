import Foundation

/// 网络请求错误类型
enum APIError: LocalizedError {
    case invalidURL
    case unauthorized
    case insufficientCredits
    case serverError(Int, String)
    case decodingError(Error)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "无效的请求地址"
        case .unauthorized: return "登录已过期，请重新登录"
        case .insufficientCredits: return "积分不足"
        case .serverError(let code, let msg): return "服务器错误 (\(code)): \(msg)"
        case .decodingError: return "数据解析失败"
        case .networkError(let error): return "网络错误: \(error.localizedDescription)"
        }
    }
}

/// API 网络请求客户端
final class APIClient {
    static let shared = APIClient()

    private let session: URLSession
    private let decoder: JSONDecoder

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        self.session = URLSession(configuration: config)
        self.decoder = JSONDecoder()
    }

    // MARK: - 通用请求方法

    /// 发送带认证的请求
    func request<T: Decodable>(
        _ path: String,
        method: String = "GET",
        body: (any Encodable)? = nil
    ) async throws -> T {
        guard let url = URL(string: Constants.baseURL + path) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // 添加 JWT token
        if let token = KeychainHelper.shared.readString(for: Constants.accessTokenKey) {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        // 添加 body
        if let body = body {
            request.httpBody = try JSONEncoder().encode(body)
        }

        do {
            let (data, response) = try await session.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.networkError(URLError(.badServerResponse))
            }

            switch httpResponse.statusCode {
            case 200...299:
                do {
                    return try decoder.decode(T.self, from: data)
                } catch {
                    throw APIError.decodingError(error)
                }
            case 401:
                throw APIError.unauthorized
            case 402:
                throw APIError.insufficientCredits
            default:
                let message = String(data: data, encoding: .utf8) ?? "未知错误"
                throw APIError.serverError(httpResponse.statusCode, message)
            }
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }

    /// 发送不带返回值的请求
    func requestVoid(
        _ path: String,
        method: String = "POST",
        body: (any Encodable)? = nil
    ) async throws {
        let _: EmptyResponse = try await request(path, method: method, body: body)
    }
}

/// 空响应（用于不需要返回内容的请求）
struct EmptyResponse: Decodable {}
