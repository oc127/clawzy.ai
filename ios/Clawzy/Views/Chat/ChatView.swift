import SwiftUI
import PhotosUI

struct ChatView: View {
    let agent: Agent
    @State private var chatService = ChatService()
    @State private var inputText = ""
    @State private var pickedImages: [Data] = []
    @State private var photoItems: [PhotosPickerItem] = []
    @State private var showAttachMenu = false
    @FocusState private var isInputFocused: Bool
    @Environment(\.lang) var lang

    var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(chatService.messages) { bubble in
                            MessageBubbleView(bubble: bubble)
                                .id(bubble.id)
                        }
                        if chatService.isStreaming && chatService.messages.last?.role != .assistant {
                            TypingIndicator()
                                .id("typing")
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                }
                .onChange(of: chatService.messages.count) {
                    withAnimation(.easeOut(duration: 0.2)) {
                        if chatService.isStreaming {
                            proxy.scrollTo("typing", anchor: .bottom)
                        } else if let lastId = chatService.messages.last?.id {
                            proxy.scrollTo(lastId, anchor: .bottom)
                        }
                    }
                }
            }

            inputBar
        }
        .background(BrandConfig.backgroundColor)
        .navigationTitle(agent.name)
        .toolbar {
            ToolbarItem(placement: .principal) {
                VStack(spacing: 1) {
                    Text(agent.name).fontWeight(.semibold)
                    HStack(spacing: 4) {
                        Circle()
                            .fill(chatService.isConnected ? Color.green : Color(white: 0.7))
                            .frame(width: 6, height: 6)
                        Text(agent.modelName)
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                }
            }
            ToolbarItem(placement: .automatic) {
                if chatService.creditBalance > 0 {
                    HStack(spacing: 3) {
                        Image(systemName: "bolt.fill").font(.caption2)
                        Text("\(chatService.creditBalance)").font(.caption).fontWeight(.medium)
                    }
                    .foregroundStyle(BrandConfig.brand)
                    .padding(.horizontal, 8).padding(.vertical, 4)
                    .background(BrandConfig.brand.opacity(0.10))
                    .clipShape(Capsule())
                }
            }
        }
        .toolbar(.visible, for: .tabBar)
        .onAppear { chatService.connect(agentId: agent.id) }
        .onDisappear { chatService.disconnect() }
        .onChange(of: photoItems) { _, newItems in
            Task {
                var loaded: [Data] = []
                for item in newItems {
                    if let data = try? await item.loadTransferable(type: Data.self) {
                        // Compress to max 1 MB
                        if let compressed = compressImage(data) {
                            loaded.append(compressed)
                        }
                    }
                }
                pickedImages.append(contentsOf: loaded)
                photoItems = []
            }
        }
    }

    // MARK: - Input bar

    private var inputBar: some View {
        VStack(spacing: 0) {
            // Image preview strip
            if !pickedImages.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(Array(pickedImages.enumerated()), id: \.offset) { idx, imgData in
                            ZStack(alignment: .topTrailing) {
                                if let uiImg = UIImage(data: imgData) {
                                    Image(uiImage: uiImg)
                                        .resizable().scaledToFill()
                                        .frame(width: 70, height: 70)
                                        .clipShape(RoundedRectangle(cornerRadius: 10))
                                }
                                Button {
                                    pickedImages.remove(at: idx)
                                } label: {
                                    Image(systemName: "xmark.circle.fill")
                                        .foregroundStyle(.white)
                                        .background(Color.black.opacity(0.5))
                                        .clipShape(Circle())
                                }
                                .offset(x: 6, y: -6)
                            }
                        }
                    }
                    .padding(.horizontal, 14)
                    .padding(.top, 10)
                }
            }

            HStack(alignment: .bottom, spacing: 8) {
                // Attachment button
                PhotosPicker(selection: $photoItems,
                             maxSelectionCount: 4,
                             matching: .images) {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 28))
                        .foregroundStyle(BrandConfig.brand.opacity(0.8))
                }

                TextField(lang.t("メッセージを入力...", en: "Type a message...", zh: "输入消息...", ko: "메시지 입력..."),
                          text: $inputText, axis: .vertical)
                    .textFieldStyle(.plain)
                    .lineLimit(1...5)
                    .focused($isInputFocused)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(Color.white)
                    .clipShape(RoundedRectangle(cornerRadius: 20))
                    .overlay(RoundedRectangle(cornerRadius: 20).stroke(Color(white: 0.86), lineWidth: 1))

                Button { sendMessage() } label: {
                    Image(systemName: "arrow.up")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundStyle(.white)
                        .frame(width: 36, height: 36)
                        .background(canSend ? BrandConfig.brand : Color(white: 0.82))
                        .clipShape(Circle())
                }
                .disabled(!canSend)
                .animation(.easeInOut(duration: 0.15), value: canSend)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
        }
        .background(BrandConfig.backgroundColor)
        .overlay(Rectangle().fill(Color(white: 0.88)).frame(height: 1), alignment: .top)
    }

    private var canSend: Bool {
        (!inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !pickedImages.isEmpty)
            && !chatService.isStreaming
    }

    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty || !pickedImages.isEmpty else { return }
        let imgs = pickedImages
        inputText = ""
        pickedImages = []
        chatService.sendMessage(text, images: imgs)
    }

    private func compressImage(_ data: Data) -> Data? {
        guard let ui = UIImage(data: data) else { return data }
        let maxBytes = 800_000
        if data.count <= maxBytes { return data }
        var quality: CGFloat = 0.8
        while quality > 0.1 {
            if let d = ui.jpegData(compressionQuality: quality), d.count <= maxBytes { return d }
            quality -= 0.15
        }
        return ui.jpegData(compressionQuality: 0.1)
    }
}

// MARK: - Message bubble

struct MessageBubbleView: View {
    let bubble: ChatBubble
    var isUser: Bool { bubble.role == .user }

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            if isUser { Spacer(minLength: 64) }

            if !isUser {
                ZStack {
                    Circle().fill(BrandConfig.brand.opacity(0.10)).frame(width: 30, height: 30)
                    Text("N")
                        .font(.system(size: 13, weight: .bold, design: .rounded))
                        .foregroundStyle(BrandConfig.brand)
                }
                .alignmentGuide(.bottom) { d in d[.bottom] }
            }

            VStack(alignment: isUser ? .trailing : .leading, spacing: 6) {
                // Image attachments
                if !bubble.images.isEmpty {
                    let cols = min(bubble.images.count, 2)
                    LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 4), count: cols), spacing: 4) {
                        ForEach(Array(bubble.images.enumerated()), id: \.offset) { _, imgData in
                            if let ui = UIImage(data: imgData) {
                                Image(uiImage: ui)
                                    .resizable().scaledToFill()
                                    .frame(width: bubble.images.count == 1 ? 200 : 95,
                                           height: bubble.images.count == 1 ? 160 : 95)
                                    .clipShape(RoundedRectangle(cornerRadius: 12))
                            }
                        }
                    }
                    .padding(4)
                    .background(isUser ? LinearGradient(colors: [BrandConfig.brand, BrandConfig.brandDeep], startPoint: .topLeading, endPoint: .bottomTrailing) : LinearGradient(colors: [Color.white], startPoint: .top, endPoint: .bottom))
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                }

                // Text content
                if !bubble.content.isEmpty {
                    Text(bubble.content)
                        .padding(.horizontal, 14).padding(.vertical, 10)
                        .background(
                            isUser
                                ? LinearGradient(colors: [BrandConfig.brand, BrandConfig.brandDeep], startPoint: .topLeading, endPoint: .bottomTrailing)
                                : LinearGradient(colors: [Color.white], startPoint: .top, endPoint: .bottom)
                        )
                        .foregroundStyle(isUser ? .white : .primary)
                        .clipShape(RoundedRectangle(cornerRadius: 18))
                        .overlay(isUser ? nil : RoundedRectangle(cornerRadius: 18).stroke(Color(white: 0.88), lineWidth: 1))
                }

                Text(bubble.timestamp, style: .time)
                    .font(.caption2).foregroundStyle(Color(white: 0.6))
            }

            if !isUser { Spacer(minLength: 64) }
        }
    }
}

// MARK: - Typing indicator

private struct TypingIndicator: View {
    @State private var phase = 0

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            ZStack {
                Circle().fill(BrandConfig.brand.opacity(0.10)).frame(width: 30, height: 30)
                Text("N").font(.system(size: 13, weight: .bold, design: .rounded)).foregroundStyle(BrandConfig.brand)
            }
            HStack(spacing: 4) {
                ForEach(0..<3) { i in
                    Circle().fill(Color(white: 0.6)).frame(width: 7, height: 7)
                        .scaleEffect(phase == i ? 1.3 : 0.8)
                        .animation(.easeInOut(duration: 0.4).repeatForever().delay(Double(i) * 0.13), value: phase)
                }
            }
            .padding(.horizontal, 14).padding(.vertical, 12)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color(white: 0.88), lineWidth: 1))
            Spacer(minLength: 64)
        }
        .onAppear { phase = 1 }
    }
}
