import SwiftUI
import PhotosUI
import PDFKit
import UniformTypeIdentifiers
import SafariServices

// MARK: - Attachment model

struct ChatAttachment: Identifiable {
    let id = UUID()
    enum AttachmentType {
        case image(Data)
        case file(name: String, text: String)
    }
    let type: AttachmentType

    var displayName: String {
        switch type {
        case .image:
                return {
                    switch Locale.current.language.languageCode?.identifier {
                    case "en": return "Image"
                    case "zh": return "图片"
                    case "ko": return "이미지"
                    default: return "画像"
                    }
                }()
        case .file(let name, _): return name
        }
    }
    var imageData: Data? {
        if case .image(let d) = type { return d }
        return nil
    }
    var fileText: String? {
        if case .file(_, let t) = type { return t }
        return nil
    }
}

// MARK: - ChatView

struct ChatView: View {
    let agent: Agent
    @State private var chatService = ChatService()
    @State private var inputText = ""
    @State private var attachments: [ChatAttachment] = []
    @State private var photoItems: [PhotosPickerItem] = []
    @State private var showPhotoPicker = false
    @State private var showFilePicker = false
    @State private var showOpenClaw = false
    @State private var showModelPicker = false
    @State private var availableModels: [AIModel] = []
    @State private var currentModelName: String = ""
    @Environment(HealthMonitor.self) var healthMonitor

    private static let allowedFileTypes: [UTType] = [
        .pdf, .plainText, .json, .commaSeparatedText,
        UTType(filenameExtension: "md")    ?? .plainText,
        UTType(filenameExtension: "swift") ?? .plainText,
        UTType(filenameExtension: "py")    ?? .plainText,
        UTType(filenameExtension: "js")    ?? .plainText,
        UTType(filenameExtension: "ts")    ?? .plainText,
    ]
    @FocusState private var isInputFocused: Bool
    @Environment(\.lang) var lang
    @Environment(\.tabBarVisible) var tabBarVisible

    var body: some View {
        VStack(spacing: 0) {
            // Disconnect banner
            if !healthMonitor.isBackendOnline || !chatService.isConnected {
                DisconnectBanner(isBackendDown: !healthMonitor.isBackendOnline)
            }
            messageList
            inputBar
        }
        .background(BrandConfig.backgroundColor)
        .navigationTitle(agent.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { toolbarContent }
        .onAppear {
            currentModelName = agent.modelName
            chatService.connect(agentId: agent.id)
            Task {
                await chatService.loadHistory(agentId: agent.id)
                await loadModels()
            }
            withAnimation(.easeInOut(duration: 0.2)) { tabBarVisible.wrappedValue = false }
        }
        .onDisappear {
            chatService.disconnect()
            withAnimation(.easeInOut(duration: 0.2)) { tabBarVisible.wrappedValue = true }
        }
        .onChange(of: photoItems) { _, newItems in
            Task { await loadPhotos(newItems) }
        }
        .fileImporter(
            isPresented: $showFilePicker,
            allowedContentTypes: Self.allowedFileTypes,
            allowsMultipleSelection: true
        ) { result in
            if case .success(let urls) = result { Task { await loadFiles(urls) } }
        }
        .photosPicker(isPresented: $showPhotoPicker, selection: $photoItems,
                      maxSelectionCount: 4, matching: .images)
        .sheet(isPresented: $showOpenClaw) {
            SafariView(url: URL(string: "https://clawzy.ai/openclaw/")!)
                .ignoresSafeArea()
        }
        .confirmationDialog(
            lang.t("モデルを選択", en: "Select Model", zh: "选择模型", ko: "모델 선택"),
            isPresented: $showModelPicker,
            titleVisibility: .visible
        ) {
            ForEach(availableModels) { model in
                Button {
                    Task { await switchModel(to: model.id) }
                } label: {
                    Text(model.name + (model.id == currentModelName ? " ✓" : ""))
                }
            }
            Button(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소"), role: .cancel) {}
        }
    }

    // MARK: - Message list

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(chatService.messages) { bubble in
                        MessageBubbleView(bubble: bubble).id(bubble.id)
                    }
                    if chatService.isStreaming && chatService.messages.last?.role != .assistant {
                        TypingIndicator().id("typing")
                    }
                }
                .padding(.horizontal, 16).padding(.vertical, 12)
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
    }

    // MARK: - Toolbar

    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem(placement: .principal) {
            VStack(spacing: 1) {
                Text(agent.name).fontWeight(.semibold)
                HStack(spacing: 4) {
                    Circle()
                        .fill(chatService.isConnected ? Color.green : Color(UIColor.systemGray3))
                        .frame(width: 6, height: 6)
                    Text(currentModelName.isEmpty ? agent.modelName : currentModelName)
                        .font(.caption2).foregroundStyle(.secondary)
                }
            }
        }
        ToolbarItem(placement: .navigationBarTrailing) {
            Button { showOpenClaw = true } label: {
                Image(systemName: "globe")
            }
        }
        ToolbarItem(placement: .navigationBarTrailing) {
            Button { showModelPicker = true } label: {
                Image(systemName: "cpu")
                    .font(.system(size: 15))
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

    // MARK: - Model switching

    private func loadModels() async {
        do {
            let models: [AIModel] = try await APIClient.shared.request(Constants.API.models)
            await MainActor.run { availableModels = models }
        } catch {
            // Silent — model picker just won't show options
        }
    }

    private func switchModel(to modelId: String) async {
        do {
            let body = UpdateAgentModelRequest(modelName: modelId)
            let _: Agent = try await APIClient.shared.request(
                Constants.API.agent(agent.id),
                method: "PATCH",
                body: body
            )
            await MainActor.run { currentModelName = modelId }
        } catch {
            // Silent fail — UI stays with previous model name
        }
    }

    // MARK: - Input bar

    private var inputBar: some View {
        VStack(spacing: 0) {
            // Attachment preview strip
            if !attachments.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(attachments) { att in
                            attachmentPreview(att)
                        }
                    }
                    .padding(.horizontal, 14).padding(.top, 10)
                }
            }

            HStack(alignment: .bottom, spacing: 8) {
                // Attach menu
                Menu {
                    Button {
                        showPhotoPicker = true
                    } label: {
                        Label(lang.t("写真・画像", en: "Photos & Images", zh: "图片", ko: "사진"), systemImage: "photo")
                    }
                    Button {
                        showFilePicker = true
                    } label: {
                        Label(lang.t("ファイル", en: "File", zh: "文件", ko: "파일"), systemImage: "doc")
                    }
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 28))
                        .foregroundStyle(attachments.isEmpty ? BrandConfig.brand.opacity(0.8) : BrandConfig.brand)
                }

                TextField(
                    lang.t("メッセージを入力...", en: "Type a message...", zh: "输入消息...", ko: "메시지 입력..."),
                    text: $inputText, axis: .vertical
                )
                .textFieldStyle(.plain).lineLimit(1...5).focused($isInputFocused)
                .padding(.horizontal, 14).padding(.vertical, 10)
                .background(BrandConfig.fieldBackground)
                .clipShape(RoundedRectangle(cornerRadius: 20))
                .overlay(RoundedRectangle(cornerRadius: 20).stroke(BrandConfig.separator, lineWidth: 1))

                Button { sendMessage() } label: {
                    Image(systemName: "arrow.up")
                        .font(.system(size: 14, weight: .bold)).foregroundStyle(.white)
                        .frame(width: 36, height: 36)
                        .background(canSend ? BrandConfig.brand : BrandConfig.disabledGray)
                        .clipShape(Circle())
                }
                .disabled(!canSend)
                .animation(.easeInOut(duration: 0.15), value: canSend)
            }
            .padding(.horizontal, 14).padding(.vertical, 10)
        }
        .background(BrandConfig.backgroundColor)
        .overlay(Rectangle().fill(BrandConfig.separator).frame(height: 0.5), alignment: .top)
    }

    @ViewBuilder
    private func attachmentPreview(_ att: ChatAttachment) -> some View {
        ZStack(alignment: .topTrailing) {
            if let imgData = att.imageData, let ui = UIImage(data: imgData) {
                Image(uiImage: ui)
                    .resizable().scaledToFill()
                    .frame(width: 70, height: 70)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
            } else {
                HStack(spacing: 6) {
                    Image(systemName: "doc.fill")
                        .foregroundStyle(BrandConfig.brand)
                    Text(att.displayName)
                        .font(.caption).lineLimit(1)
                        .frame(maxWidth: 100)
                }
                .padding(.horizontal, 10).padding(.vertical, 12)
                .background(BrandConfig.brand.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .frame(height: 70)
            }

            Button {
                attachments.removeAll { $0.id == att.id }
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .foregroundStyle(.white)
                    .background(Color.black.opacity(0.5))
                    .clipShape(Circle())
            }
            .offset(x: 6, y: -6)
        }
    }

    // MARK: - Send logic

    private var canSend: Bool {
        (!inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !attachments.isEmpty)
            && !chatService.isStreaming
    }

    private func sendMessage() {
        var text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        let imgs = attachments.compactMap(\.imageData)
        let files = attachments.filter { $0.fileText != nil }

        guard !text.isEmpty || !imgs.isEmpty || !files.isEmpty else { return }

        // Append file content to text
        for file in files {
            if let content = file.fileText {
                text += "\n\n📄 **\(file.displayName)**\n```\n\(content.prefix(8000))\n```"
            }
        }

        inputText = ""
        attachments = []
        chatService.sendMessage(text, images: imgs)
    }

    // MARK: - Loading helpers

    private func loadPhotos(_ items: [PhotosPickerItem]) async {
        for item in items {
            if let data = try? await item.loadTransferable(type: Data.self),
               let compressed = compressImage(data) {
                attachments.append(ChatAttachment(type: .image(compressed)))
            }
        }
        photoItems = []
    }

    private func loadFiles(_ urls: [URL]) async {
        for url in urls {
            guard url.startAccessingSecurityScopedResource() else { continue }
            defer { url.stopAccessingSecurityScopedResource() }

            let name = url.lastPathComponent
            let ext = url.pathExtension.lowercased()

            if ext == "pdf" {
                if let doc = PDFDocument(url: url) {
                    var text = ""
                    for i in 0..<min(doc.pageCount, 30) {
                        text += doc.page(at: i)?.string ?? ""
                    }
                    await MainActor.run {
                        attachments.append(ChatAttachment(type: .file(name: name, text: text)))
                    }
                }
            } else {
                if let text = try? String(contentsOf: url, encoding: .utf8) {
                    await MainActor.run {
                        attachments.append(ChatAttachment(type: .file(name: name, text: text)))
                    }
                }
            }
        }
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

// MARK: - Disconnect banner

private struct DisconnectBanner: View {
    let isBackendDown: Bool
    @Environment(\.lang) var lang

    var body: some View {
        HStack(spacing: 8) {
            ProgressView()
                .scaleEffect(0.8)
                .tint(.white)
            Text(isBackendDown
                 ? lang.t("サーバーに接続できません", en: "Server unreachable", zh: "服务器无法访问", ko: "서버 연결 불가")
                 : lang.t("接続中断、再接続中...", en: "Connection lost, reconnecting...", zh: "连接中断，正在重连...", ko: "연결 끊김, 재연결 중..."))
                .font(.caption)
                .fontWeight(.medium)
                .foregroundStyle(.white)
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(isBackendDown ? Color.red : Color.orange)
        .transition(.move(edge: .top).combined(with: .opacity))
        .animation(.easeInOut, value: isBackendDown)
    }
}

// MARK: - Model update request

private struct UpdateAgentModelRequest: Encodable {
    let modelName: String
    enum CodingKeys: String, CodingKey {
        case modelName = "model_name"
    }
}

// MARK: - Safari wrapper

struct SafariView: UIViewControllerRepresentable {
    let url: URL
    func makeUIViewController(context: Context) -> SFSafariViewController {
        SFSafariViewController(url: url)
    }
    func updateUIViewController(_ uiViewController: SFSafariViewController, context: Context) {}
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
                // Image grid
                if !bubble.images.isEmpty {
                    ImageGridView(images: bubble.images, isUser: isUser)
                }

                // Text bubble
                if !bubble.content.isEmpty {
                    TextBubbleView(text: bubble.content, isUser: isUser)
                }

                Text(bubble.timestamp, style: .time)
                    .font(.caption2).foregroundStyle(.secondary)
            }

            if !isUser { Spacer(minLength: 64) }
        }
    }
}

// MARK: - Text bubble

private struct TextBubbleView: View {
    let text: String
    let isUser: Bool

    private var bg: LinearGradient {
        isUser
            ? LinearGradient(colors: [BrandConfig.brand, BrandConfig.brandDeep],
                             startPoint: .topLeading, endPoint: .bottomTrailing)
            : LinearGradient(colors: [BrandConfig.cardBackground], startPoint: .top, endPoint: .bottom)
    }

    var body: some View {
        Text(text)
            .padding(.horizontal, 14).padding(.vertical, 10)
            .background(bg)
            .foregroundStyle(isUser ? .white : .primary)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .overlay(
                isUser ? nil : RoundedRectangle(cornerRadius: 18).stroke(BrandConfig.separator, lineWidth: 1)
            )
    }
}

// MARK: - Image grid

private struct ImageGridView: View {
    let images: [Data]
    let isUser: Bool

    private var cols: Int { min(images.count, 2) }
    private var imgSize: CGSize {
        images.count == 1 ? CGSize(width: 200, height: 160) : CGSize(width: 95, height: 95)
    }
    private var bg: LinearGradient {
        isUser
            ? LinearGradient(colors: [BrandConfig.brand, BrandConfig.brandDeep],
                             startPoint: .topLeading, endPoint: .bottomTrailing)
            : LinearGradient(colors: [BrandConfig.cardBackground], startPoint: .top, endPoint: .bottom)
    }

    var body: some View {
        LazyVGrid(
            columns: Array(repeating: GridItem(.flexible(), spacing: 4), count: cols),
            spacing: 4
        ) {
            ForEach(Array(images.enumerated()), id: \.offset) { _, imgData in
                if let ui = UIImage(data: imgData) {
                    Image(uiImage: ui)
                        .resizable().scaledToFill()
                        .frame(width: imgSize.width, height: imgSize.height)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }
            }
        }
        .padding(4)
        .background(bg)
        .clipShape(RoundedRectangle(cornerRadius: 16))
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
                    Circle().fill(Color.secondary).frame(width: 7, height: 7)
                        .scaleEffect(phase == i ? 1.3 : 0.8)
                        .animation(.easeInOut(duration: 0.4).repeatForever().delay(Double(i) * 0.13), value: phase)
                }
            }
            .padding(.horizontal, 14).padding(.vertical, 12)
            .background(BrandConfig.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(BrandConfig.separator, lineWidth: 1))
            Spacer(minLength: 64)
        }
        .onAppear { phase = 1 }
    }
}
