import Foundation

/// 全局 ChatService 缓存 — 按 agentId 索引，切换页面时保持 WebSocket 连接不断开
@Observable
final class ChatServiceCache {
    private var services: [String: ChatService] = [:]

    func service(for agentId: String) -> ChatService {
        if let existing = services[agentId] { return existing }
        let s = ChatService()
        services[agentId] = s
        return s
    }
}
