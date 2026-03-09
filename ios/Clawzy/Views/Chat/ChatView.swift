import SwiftUI

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var messages: [DisplayMessage] = []
    @Published var streamingContent = ""
    @Published var isStreaming = false
    @Published var connectionStatus: WebSocketClient.ConnectionStatus = .disconnected
    @Published var creditBalance: Int?

    private var wsClient: WebSocketClient?
    let agent: Agent

    struct DisplayMessage: Identifiable {
        let id = UUID()
        let role: MessageRole
        let content: String
    }

    init(agent: Agent) {
        self.agent = agent
    }

    func connect() {
        wsClient = WebSocketClient(agentId: agent.id) { [weak self] msg in
            Task { @MainActor in
                self?.handleMessage(msg)
            }
        }
        wsClient?.connect()

        // Observe connection status
        Task {
            while !Task.isCancelled {
                connectionStatus = wsClient?.status ?? .disconnected
                try? await Task.sleep(for: .milliseconds(500))
            }
        }
    }

    func disconnect() {
        wsClient?.disconnect()
        wsClient = nil
    }

    func sendMessage(_ text: String) {
        guard !text.isEmpty else { return }
        messages.append(DisplayMessage(role: .user, content: text))
        streamingContent = ""
        isStreaming = true
        wsClient?.sendMessage(text)
    }

    private func handleMessage(_ msg: ChatMessage) {
        switch msg.type {
        case .stream:
            streamingContent += msg.content ?? ""

        case .done:
            if !streamingContent.isEmpty {
                messages.append(DisplayMessage(role: .assistant, content: streamingContent))
            }
            streamingContent = ""
            isStreaming = false
            if let balance = msg.usage?.balance {
                creditBalance = balance
            }

        case .error:
            let errorText = msg.message ?? msg.content ?? "An error occurred."
            messages.append(DisplayMessage(role: .assistant, content: "Error: \(errorText)"))
            streamingContent = ""
            isStreaming = false

        case .status, .agent_status:
            // Could show agent status updates in UI
            break

        case .model_switched:
            break

        default:
            break
        }
    }

    func loadHistory() async {
        do {
            let convos: [Conversation] = try await APIClient.shared.request(
                path: "/agents/\(agent.id)/conversations"
            )
            guard let latest = convos.first else { return }
            let history: [Message] = try await APIClient.shared.request(
                path: "/conversations/\(latest.id)/messages?limit=50"
            )
            messages = history.map {
                DisplayMessage(role: $0.role, content: $0.content)
            }
        } catch {
            // No history — start fresh
        }
    }
}

struct ChatView: View {
    let agent: Agent
    @StateObject private var vm: ChatViewModel
    @State private var inputText = ""
    @FocusState private var inputFocused: Bool

    init(agent: Agent) {
        self.agent = agent
        _vm = StateObject(wrappedValue: ChatViewModel(agent: agent))
    }

    var body: some View {
        VStack(spacing: 0) {
            // Connection status bar
            if vm.connectionStatus == .connecting {
                HStack(spacing: 6) {
                    ProgressView()
                        .controlSize(.small)
                    Text("Connecting…")
                        .font(.caption)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 4)
                .background(.orange.opacity(0.1))
            }

            // Messages
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(vm.messages) { message in
                            MessageBubble(message: message)
                                .id(message.id)
                        }

                        // Streaming indicator
                        if !vm.streamingContent.isEmpty {
                            MessageBubble(
                                message: ChatViewModel.DisplayMessage(
                                    role: .assistant,
                                    content: vm.streamingContent
                                )
                            )
                            .id("streaming")
                        }
                    }
                    .padding()
                }
                .onChange(of: vm.messages.count) {
                    if let last = vm.messages.last {
                        withAnimation {
                            proxy.scrollTo(last.id, anchor: .bottom)
                        }
                    }
                }
                .onChange(of: vm.streamingContent) {
                    withAnimation {
                        proxy.scrollTo("streaming", anchor: .bottom)
                    }
                }
            }

            Divider()

            // Input bar
            HStack(spacing: 8) {
                TextField("Type a message…", text: $inputText, axis: .vertical)
                    .textFieldStyle(.plain)
                    .lineLimit(1...5)
                    .focused($inputFocused)
                    .onSubmit {
                        sendMessage()
                    }

                Button {
                    sendMessage()
                } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title2)
                }
                .disabled(inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || vm.isStreaming)
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
        }
        .navigationTitle(agent.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                if let balance = vm.creditBalance {
                    Text("\(balance) credits")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .task {
            await vm.loadHistory()
            vm.connect()
        }
        .onDisappear {
            vm.disconnect()
        }
    }

    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        vm.sendMessage(text)
        inputText = ""
    }
}

// MARK: - Message Bubble

struct MessageBubble: View {
    let message: ChatViewModel.DisplayMessage

    private var isUser: Bool { message.role == .user }

    var body: some View {
        HStack {
            if isUser { Spacer(minLength: 60) }

            Text(message.content)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(isUser ? Color.accentColor : Color(.systemGray5))
                .foregroundStyle(isUser ? .white : .primary)
                .clipShape(RoundedRectangle(cornerRadius: 16))

            if !isUser { Spacer(minLength: 60) }
        }
    }
}
