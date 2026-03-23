import Foundation
import Observation

/// WebSocket 聊天服务
@Observable
final class ChatService {
    var messages: [ChatBubble] = []
    var isConnected = false
    var isStreaming = false
    var creditBalance: Int = 0

    private var webSocketTask: URLSessionWebSocketTask?
    private var currentStreamText = ""

    // MARK: - 连接

    func connect(agentId: String) {
        guard let token = KeychainHelper.shared.readString(for: Constants.accessTokenKey) else { return }
        let urlString = Constants.wsBaseURL + Constants.API.wsChat(agentId) + "?token=\(token)"
        guard let url = URL(string: urlString) else { return }
        webSocketTask = URLSession.shared.webSocketTask(with: url)
        webSocketTask?.resume()
        isConnected = true
        receiveMessage()
    }

    func disconnect() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        isConnected = false
    }

    // MARK: - 发送消息

    func sendMessage(_ content: String) {
        let userBubble = ChatBubble(role: .user, content: content)
        messages.append(userBubble)
        let msg = WSSendMessage(type: "message", content: content, model: nil)
        guard let data = try? JSONEncoder().encode(msg),
              let string = String(data: data, encoding: .utf8) else { return }
        webSocketTask?.send(.string(string)) { error in
            if let error = error { print("WebSocket 发送失败: \(error)") }
        }
        isStreaming = true
        currentStreamText = ""
        // Don't pre-append assistant bubble — it's added on first stream chunk
    }

    // MARK: - 接收消息

    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            Task { @MainActor [weak self] in
                guard let self else { return }
                switch result {
                case .success(let message):
                    if case .string(let text) = message { self.handleReceivedText(text) }
                    self.receiveMessage()
                case .failure(let error):
                    print("WebSocket 接收失败: \(error)")
                    self.isConnected = false
                }
            }
        }
    }

    private func handleReceivedText(_ text: String) {
        guard let data = text.data(using: .utf8),
              let raw = try? JSONDecoder().decode(WSRawMessage.self, from: data) else { return }
        switch raw.type {
        case "stream":
            if let content = raw.content {
                currentStreamText += content
                if let lastIndex = messages.indices.last, messages[lastIndex].role == .assistant {
                    messages[lastIndex].content = currentStreamText
                } else {
                    messages.append(ChatBubble(role: .assistant, content: currentStreamText))
                }
            }
        case "done":
            isStreaming = false
            if let usage = raw.usage { creditBalance = usage.balance }
        case "error":
            isStreaming = false
            if let lastIndex = messages.indices.last {
                messages[lastIndex].content = "⚠️ \(raw.message ?? "发生未知错误")"
            }
        default:
            break
        }
    }

    // MARK: - 加载历史对话

    func loadConversations(agentId: String) async -> [Conversation] {
        (try? await APIClient.shared.request(Constants.API.conversations(agentId))) ?? []
    }

    func loadMessages(conversationId: String) async -> [Message] {
        (try? await APIClient.shared.request(Constants.API.messages(conversationId))) ?? []
    }
}

/// 聊天气泡（用于 UI 显示）
struct ChatBubble: Identifiable {
    let id = UUID()
    let role: MessageRole
    var content: String
    let timestamp = Date()
}
