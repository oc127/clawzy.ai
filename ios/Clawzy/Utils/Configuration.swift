import Foundation

enum Configuration {
    static let apiBaseURL: String = {
        if let url = ProcessInfo.processInfo.environment["CLAWZY_API_URL"] {
            return url
        }
        #if DEBUG
        return "http://localhost:8000/api/v1"
        #else
        return "https://clawzy.ai/api/v1"
        #endif
    }()

    static var wsBaseURL: String {
        apiBaseURL
            .replacingOccurrences(of: "https://", with: "wss://")
            .replacingOccurrences(of: "http://", with: "ws://")
    }
}
