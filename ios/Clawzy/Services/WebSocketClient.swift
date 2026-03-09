import Foundation

/// Real-time chat WebSocket client mirroring the web `ws.ts`.
/// Supports auto-reconnect with exponential backoff and ping keepalive.
@MainActor
final class WebSocketClient: ObservableObject {
    enum ConnectionStatus: Equatable {
        case disconnected
        case connecting
        case connected
    }

    @Published private(set) var status: ConnectionStatus = .disconnected

    private let agentId: String
    private let onMessage: (ChatMessage) -> Void

    private var task: URLSessionWebSocketTask?
    private var reconnectAttempts = 0
    private var intentionallyClosed = false
    private var pingTimer: Timer?

    private let maxReconnect = 10
    private let baseDelay: TimeInterval = 1.0

    init(agentId: String, onMessage: @escaping (ChatMessage) -> Void) {
        self.agentId = agentId
        self.onMessage = onMessage
    }

    // MARK: - Public

    func connect() {
        intentionallyClosed = false
        doConnect()
    }

    func disconnect() {
        intentionallyClosed = true
        pingTimer?.invalidate()
        pingTimer = nil
        task?.cancel(with: .normalClosure, reason: nil)
        task = nil
        status = .disconnected
    }

    func send(_ message: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: message),
              let text = String(data: data, encoding: .utf8) else { return }
        task?.send(.string(text)) { _ in }
    }

    func sendMessage(_ content: String) {
        send(["type": "message", "content": content])
    }

    func switchModel(_ model: String) {
        send(["type": "switch_model", "model": model])
    }

    // MARK: - Internal

    private func doConnect() {
        guard let token = AuthService.shared.accessToken else {
            status = .disconnected
            return
        }

        status = .connecting
        let urlString = "\(Configuration.wsBaseURL)/ws/chat/\(agentId)?token=\(token)&locale=en"
        guard let url = URL(string: urlString) else { return }

        task = URLSession.shared.webSocketTask(with: url)
        task?.resume()

        // Consider connected once the first receive succeeds
        status = .connected
        reconnectAttempts = 0
        startPing()
        receiveLoop()
    }

    private func receiveLoop() {
        task?.receive { [weak self] result in
            Task { @MainActor in
                guard let self, !self.intentionallyClosed else { return }
                switch result {
                case .success(let message):
                    self.handleMessage(message)
                    self.receiveLoop()
                case .failure:
                    self.handleDisconnect()
                }
            }
        }
    }

    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            guard let data = text.data(using: .utf8),
                  let msg = try? JSONDecoder().decode(ChatMessage.self, from: data) else { return }
            if msg.type != .pong {
                onMessage(msg)
            }
        case .data(let data):
            guard let msg = try? JSONDecoder().decode(ChatMessage.self, from: data) else { return }
            if msg.type != .pong {
                onMessage(msg)
            }
        @unknown default:
            break
        }
    }

    private func handleDisconnect() {
        pingTimer?.invalidate()
        pingTimer = nil

        guard !intentionallyClosed else {
            status = .disconnected
            return
        }

        guard reconnectAttempts < maxReconnect else {
            status = .disconnected
            return
        }

        let delay = min(baseDelay * pow(2.0, Double(reconnectAttempts)), 30.0)
        reconnectAttempts += 1
        status = .connecting

        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(delay))
            self?.doConnect()
        }
    }

    private func startPing() {
        pingTimer?.invalidate()
        pingTimer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.send(["type": "ping"])
            }
        }
    }
}
