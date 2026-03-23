import SwiftUI

struct ChatView: View {
    let agent: Agent
    @State private var chatService = ChatService()
    @State private var inputText = ""
    @FocusState private var isInputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(chatService.messages) { bubble in
                            MessageBubbleView(bubble: bubble)
                                .id(bubble.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: chatService.messages.count) {
                    if let lastId = chatService.messages.last?.id {
                        withAnimation { proxy.scrollTo(lastId, anchor: .bottom) }
                    }
                }
            }

            Divider()

            HStack(spacing: 12) {
                TextField("输入消息...", text: $inputText, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(1...5)
                    .focused($isInputFocused)

                Button { sendMessage() } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title2)
                        .foregroundStyle(canSend ? .orange : .gray)
                }
                .disabled(!canSend)
            }
            .padding()
        }
        .navigationTitle(agent.name)
        .toolbar {
            ToolbarItem(placement: .principal) {
                VStack(spacing: 2) {
                    Text(agent.name).fontWeight(.semibold)
                    HStack(spacing: 4) {
                        Circle()
                            .fill(chatService.isConnected ? Color.green : Color.red)
                            .frame(width: 6, height: 6)
                        Text(agent.modelName)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            ToolbarItem(placement: .automatic) {
                if chatService.creditBalance > 0 {
                    Text("\(chatService.creditBalance) 积分")
                        .font(.caption)
                        .foregroundStyle(.orange)
                }
            }
        }
        .onAppear { chatService.connect(agentId: agent.id) }
        .onDisappear { chatService.disconnect() }
    }

    private var canSend: Bool {
        !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && chatService.isConnected && !chatService.isStreaming
    }

    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        inputText = ""
        chatService.sendMessage(text)
    }
}

struct MessageBubbleView: View {
    let bubble: ChatBubble
    var isUser: Bool { bubble.role == .user }

    var body: some View {
        HStack {
            if isUser { Spacer(minLength: 60) }
            VStack(alignment: isUser ? .trailing : .leading, spacing: 4) {
                Text(bubble.content)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(isUser ? Color.orange : Color.gray.opacity(0.15))
                    .foregroundStyle(isUser ? .white : .primary)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                Text(bubble.timestamp, style: .time)
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
            if !isUser { Spacer(minLength: 60) }
        }
    }
}
