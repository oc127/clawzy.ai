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
    @State private var showConversationList = false
    @State private var showSkillsPanel = false
    @State private var showCameraComingSoon = false
    @State private var pluginsStore = PluginsStore()
    @State private var conversations: [Conversation] = []
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
                await loadConversations()
                await pluginsStore.fetch(agentId: agent.id)
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
        .sheet(isPresented: $showModelPicker) {
            ModelPickerView(
                models: availableModels,
                currentModelId: currentModelName,
                onSelect: { modelId in
                    Task { await switchModel(to: modelId) }
                    showModelPicker = false
                }
            )
            .presentationDetents([.medium])
            .presentationDragIndicator(.visible)
        }
        .sheet(isPresented: $showConversationList) {
            ConversationListView(
                conversations: conversations,
                currentConversationId: chatService.currentConversationId,
                onSelect: { conversation in
                    showConversationList = false
                    Task { await chatService.switchConversation(conversation) }
                },
                onNewConversation: {
                    showConversationList = false
                    chatService.startNewConversation()
                }
            )
            .presentationDetents([.medium, .large])
            .presentationDragIndicator(.visible)
        }
        .sheet(isPresented: $showSkillsPanel) {
            SkillsPanelView(
                plugins: pluginsStore.plugins(for: agent.id),
                onSendSkill: { message in
                    showSkillsPanel = false
                    sendPresetMessage(message)
                }
            )
            .presentationDetents([.medium])
            .presentationDragIndicator(.visible)
        }
        .alert(lang.t("カメラ機能", en: "Camera", zh: "拍照", ko: "카메라"), isPresented: $showCameraComingSoon) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(lang.t("カメラ機能は近日公開予定です", en: "Camera feature coming soon", zh: "拍照功能即将推出", ko: "카메라 기능 준비 중"))
        }
    }

    // MARK: - Message list

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 0) {
                    ForEach(chatService.messages) { bubble in
                        MessageBubbleView(bubble: bubble).id(bubble.id)
                    }
                    if chatService.isStreaming && chatService.messages.last?.role != .assistant {
                        TypingIndicator().id("typing")
                    }
                    Color.clear.frame(height: 1).id("bottom")
                }
                .padding(.horizontal, 16).padding(.top, 12)
            }
            .scrollDismissesKeyboard(.interactively)
            .onTapGesture { UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil) }
            .onChange(of: chatService.messages.count) {
                withAnimation(.easeOut(duration: 0.15)) {
                    proxy.scrollTo("bottom", anchor: .bottom)
                }
            }
            .onChange(of: chatService.isStreaming) { _, streaming in
                if !streaming {
                    withAnimation(.easeOut(duration: 0.15)) {
                        proxy.scrollTo("bottom", anchor: .bottom)
                    }
                }
            }
        }
    }

    // MARK: - Toolbar

    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem(placement: .principal) {
            Button {
                Task { await loadConversations() }
                showConversationList = true
            } label: {
                VStack(spacing: 1) {
                    HStack(spacing: 4) {
                        Text(agent.name).fontWeight(.semibold)
                            .foregroundStyle(.primary)
                        Image(systemName: "chevron.down")
                            .font(.system(size: 9, weight: .bold))
                            .foregroundStyle(.secondary)
                    }
                    if let title = chatService.currentConversationTitle, !title.isEmpty {
                        let isNewConvo = title == "New conversation"
                        Text(title)
                            .font(.caption2)
                            .foregroundStyle(isNewConvo ? .tertiary : .secondary)
                            .italic(isNewConvo)
                            .lineLimit(1)
                    } else {
                        HStack(spacing: 4) {
                            Circle()
                                .fill(chatService.isConnected ? Color.green : Color(UIColor.systemGray3))
                                .frame(width: 6, height: 6)
                            Text(lang.t("新しい会話", en: "New conversation", zh: "新对话", ko: "새 대화"))
                                .font(.caption2).foregroundStyle(.tertiary)
                                .italic()
                        }
                    }
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
                HStack(spacing: 3) {
                    Circle()
                        .fill(chatService.isConnected ? Color.green : Color(UIColor.systemGray3))
                        .frame(width: 5, height: 5)
                    Text(shortModelName(currentModelName.isEmpty ? agent.modelName : currentModelName))
                        .font(.caption2).fontWeight(.medium)
                }
                .padding(.horizontal, 8).padding(.vertical, 4)
                .background(Color(UIColor.systemGray5))
                .clipShape(Capsule())
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

    private func shortModelName(_ name: String) -> String {
        if name.count > 16 {
            return String(name.prefix(14)) + "..."
        }
        return name
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

    private func loadConversations() async {
        let loaded = await chatService.loadConversations(agentId: agent.id)
        await MainActor.run { conversations = loaded }
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

            HStack(alignment: .bottom, spacing: 6) {
                // ⊕ Attach button
                Menu {
                    Button {
                        showCameraComingSoon = true
                    } label: {
                        Label(lang.t("写真を撮る", en: "Take Photo", zh: "拍照", ko: "사진 찍기"), systemImage: "camera")
                    }
                    Button {
                        showPhotoPicker = true
                    } label: {
                        Label(lang.t("アルバムから選ぶ", en: "Photo Library", zh: "从相册选择", ko: "앨범에서 선택"), systemImage: "photo")
                    }
                    Button {
                        showFilePicker = true
                    } label: {
                        Label(lang.t("ファイルを選ぶ", en: "Choose File", zh: "选择文件", ko: "파일 선택"), systemImage: "doc")
                    }
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 26))
                        .foregroundStyle(attachments.isEmpty ? BrandConfig.brand.opacity(0.8) : BrandConfig.brand)
                }

                // 🎵 Skills button
                Button {
                    showSkillsPanel = true
                } label: {
                    Image(systemName: "wand.and.stars")
                        .font(.system(size: 22))
                        .foregroundStyle(BrandConfig.brand.opacity(0.8))
                        .frame(width: 28, height: 28)
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

            // AI generated content disclaimer
            Text(lang.t("内容はAIが生成しています", en: "AI-generated content", zh: "内容由AI生成", ko: "AI 생성 콘텐츠"))
                .font(.system(size: 11))
                .foregroundStyle(.tertiary)
                .padding(.bottom, 8)
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

        for file in files {
            if let content = file.fileText {
                text += "\n\n📄 **\(file.displayName)**\n```\n\(content.prefix(8000))\n```"
            }
        }

        inputText = ""
        attachments = []
        chatService.sendMessage(text, images: imgs)
    }

    private func sendPresetMessage(_ text: String) {
        guard !chatService.isStreaming else { return }
        chatService.sendMessage(text, images: [])
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
        if isUser {
            // User message: right-aligned with subtle background, wide but not full-bleed
            HStack(alignment: .bottom, spacing: 8) {
                Spacer(minLength: 48)
                VStack(alignment: .trailing, spacing: 4) {
                    if !bubble.images.isEmpty {
                        ImageGridView(images: bubble.images, isUser: true)
                    }
                    if !bubble.content.isEmpty {
                        Text(bubble.content)
                            .textSelection(.enabled)
                            .padding(.horizontal, 14).padding(.vertical, 10)
                            .background(BrandConfig.brand.opacity(0.10))
                            .foregroundStyle(.primary)
                            .clipShape(RoundedRectangle(cornerRadius: 18))
                    }
                    Text(bubble.timestamp, style: .time)
                        .font(.caption2).foregroundStyle(.tertiary)
                }
            }
            .padding(.bottom, 12)
        } else {
            // AI message: full-width, no bubble, avatar on left
            VStack(alignment: .leading, spacing: 0) {
                Divider()
                    .padding(.bottom, 10)
                HStack(alignment: .top, spacing: 10) {
                    ZStack {
                        Circle()
                            .fill(BrandConfig.brand.opacity(0.10))
                            .frame(width: 28, height: 28)
                        Text("N")
                            .font(.system(size: 12, weight: .bold, design: .rounded))
                            .foregroundStyle(BrandConfig.brand)
                    }
                    VStack(alignment: .leading, spacing: 6) {
                        if !bubble.images.isEmpty {
                            ImageGridView(images: bubble.images, isUser: false)
                        }
                        if !bubble.content.isEmpty {
                            Text(LocalizedStringKey(bubble.content))
                                .textSelection(.enabled)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .foregroundStyle(.primary)
                        }
                        Text(bubble.timestamp, style: .time)
                            .font(.caption2).foregroundStyle(.tertiary)
                    }
                }
                .padding(.bottom, 12)
            }
        }
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
        .background(BrandConfig.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }
}

// MARK: - Typing indicator

private struct TypingIndicator: View {
    @State private var phase = 0

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Divider()
                .padding(.bottom, 10)
            HStack(alignment: .top, spacing: 10) {
                ZStack {
                    Circle().fill(BrandConfig.brand.opacity(0.10)).frame(width: 28, height: 28)
                    Text("N").font(.system(size: 12, weight: .bold, design: .rounded)).foregroundStyle(BrandConfig.brand)
                }
                HStack(spacing: 4) {
                    ForEach(0..<3) { i in
                        Circle().fill(Color.secondary).frame(width: 7, height: 7)
                            .scaleEffect(phase == i ? 1.3 : 0.8)
                            .animation(.easeInOut(duration: 0.4).repeatForever().delay(Double(i) * 0.13), value: phase)
                    }
                }
                .padding(.top, 6)
            }
            .padding(.bottom, 12)
        }
        .onAppear { phase = 1 }
    }
}

// MARK: - Skills Panel

private struct BuiltinSkill: Identifiable {
    let id = UUID()
    let icon: String
    let name: String
    let description: String
    let prompt: String
}

struct SkillsPanelView: View {
    let plugins: [InstalledPlugin]
    let onSendSkill: (String) -> Void
    @Environment(\.lang) var lang

    private var builtinSkills: [BuiltinSkill] {
        [
            BuiltinSkill(
                icon: "newspaper.fill",
                name: lang.t("AI日報速覧", en: "AI Daily Brief", zh: "AI日报速览", ko: "AI 일일 브리핑"),
                description: lang.t("今日のAIニュースを要約", en: "Summarize today's AI news", zh: "总结今日AI新闻", ko: "오늘의 AI 뉴스 요약"),
                prompt: "今日のAIニュースを要約してください"
            ),
            BuiltinSkill(
                icon: "tablecells.fill",
                name: "XLSX",
                description: lang.t("Excelファイルを作成・処理", en: "Create or process Excel files", zh: "创建或处理Excel文件", ko: "Excel 파일 생성/처리"),
                prompt: "Excelファイルを作成してください"
            ),
            BuiltinSkill(
                icon: "doc.richtext.fill",
                name: "PDF",
                description: lang.t("PDFを処理・生成", en: "Process or generate PDFs", zh: "处理或生成PDF", ko: "PDF 처리/생성"),
                prompt: "PDFを処理してください"
            ),
        ]
    }

    var body: some View {
        NavigationStack {
            List {
                Section(lang.t("ビルトインスキル", en: "Built-in Skills", zh: "内置技能", ko: "기본 기술")) {
                    ForEach(builtinSkills) { skill in
                        Button {
                            onSendSkill(skill.prompt)
                        } label: {
                            HStack(spacing: 12) {
                                ZStack {
                                    RoundedRectangle(cornerRadius: 8)
                                        .fill(BrandConfig.brand.opacity(0.12))
                                        .frame(width: 36, height: 36)
                                    Image(systemName: skill.icon)
                                        .font(.system(size: 16))
                                        .foregroundStyle(BrandConfig.brand)
                                }
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(skill.name)
                                        .font(.subheadline).fontWeight(.medium)
                                        .foregroundStyle(.primary)
                                    Text(skill.description)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .font(.caption)
                                    .foregroundStyle(.tertiary)
                            }
                            .padding(.vertical, 2)
                        }
                    }
                }

                if !plugins.isEmpty {
                    Section(lang.t("インストール済みスキル", en: "Installed Skills", zh: "已安装技能", ko: "설치된 기술")) {
                        ForEach(plugins) { plugin in
                            Button {
                                let displayName = plugin.name ?? plugin.slug
                                onSendSkill("「\(displayName)」スキルを使ってください")
                            } label: {
                                HStack(spacing: 12) {
                                    ZStack {
                                        RoundedRectangle(cornerRadius: 8)
                                            .fill(Color.purple.opacity(0.10))
                                            .frame(width: 36, height: 36)
                                        Image(systemName: "puzzlepiece.extension.fill")
                                            .font(.system(size: 16))
                                            .foregroundStyle(Color.purple)
                                    }
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(plugin.name ?? plugin.slug)
                                            .font(.subheadline).fontWeight(.medium)
                                            .foregroundStyle(.primary)
                                        Text(plugin.slug)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                    Spacer()
                                    Image(systemName: "chevron.right")
                                        .font(.caption)
                                        .foregroundStyle(.tertiary)
                                }
                                .padding(.vertical, 2)
                            }
                        }
                    }
                }
            }
            .navigationTitle(lang.t("スキル", en: "Skills", zh: "技能", ko: "기술"))
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

// MARK: - Conversation List View

struct ConversationListView: View {
    let conversations: [Conversation]
    let currentConversationId: String?
    let onSelect: (Conversation) -> Void
    let onNewConversation: () -> Void
    @Environment(\.lang) var lang

    var body: some View {
        NavigationStack {
            List {
                Button {
                    onNewConversation()
                } label: {
                    HStack(spacing: 10) {
                        Image(systemName: "plus.circle.fill")
                            .foregroundStyle(BrandConfig.brand)
                            .font(.title3)
                        Text(lang.t("新しい会話", en: "New conversation", zh: "新对话", ko: "새 대화"))
                            .fontWeight(.medium)
                        Spacer()
                    }
                    .padding(.vertical, 4)
                }

                if conversations.isEmpty {
                    HStack {
                        Spacer()
                        VStack(spacing: 8) {
                            Image(systemName: "bubble.left.and.bubble.right")
                                .font(.largeTitle)
                                .foregroundStyle(.tertiary)
                            Text(lang.t("会話履歴はありません", en: "No conversations yet", zh: "暂无对话记录", ko: "대화 기록 없음"))
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 32)
                        Spacer()
                    }
                    .listRowBackground(Color.clear)
                } else {
                    ForEach(conversations) { conversation in
                        Button {
                            onSelect(conversation)
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(conversation.title)
                                        .font(.subheadline)
                                        .fontWeight(.medium)
                                        .lineLimit(2)
                                        .foregroundStyle(.primary)
                                    Text(formatDate(conversation.updatedAt))
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                if conversation.id == currentConversationId {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundStyle(BrandConfig.brand)
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
            }
            .navigationTitle(lang.t("会話一覧", en: "Conversations", zh: "对话列表", ko: "대화 목록"))
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private func formatDate(_ isoString: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard let date = formatter.date(from: isoString) ?? ISO8601DateFormatter().date(from: isoString) else {
            return isoString
        }
        let relative = RelativeDateTimeFormatter()
        relative.unitsStyle = .short
        return relative.localizedString(for: date, relativeTo: Date())
    }
}

// MARK: - Model Picker View

struct ModelPickerView: View {
    let models: [AIModel]
    let currentModelId: String
    let onSelect: (String) -> Void
    @Environment(\.lang) var lang

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(spacing: 10) {
                    ForEach(models) { model in
                        let isSelected = model.id == currentModelId
                        Button {
                            onSelect(model.id)
                        } label: {
                            HStack(alignment: .top, spacing: 12) {
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack(spacing: 6) {
                                        Text(model.name)
                                            .font(.subheadline)
                                            .fontWeight(.semibold)
                                            .foregroundStyle(.primary)
                                        Text(model.tier.uppercased())
                                            .font(.system(size: 9, weight: .bold))
                                            .padding(.horizontal, 5).padding(.vertical, 2)
                                            .background(tierColor(model.tier).opacity(0.15))
                                            .foregroundStyle(tierColor(model.tier))
                                            .clipShape(RoundedRectangle(cornerRadius: 4))
                                    }
                                    Text(model.description)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                        .lineLimit(2)
                                    HStack(spacing: 12) {
                                        Label(
                                            lang.t("入力", en: "In", zh: "输入", ko: "입력") + ": \(String(format: "%.1f", model.creditsPerInputK))",
                                            systemImage: "arrow.down.circle"
                                        )
                                        Label(
                                            lang.t("出力", en: "Out", zh: "输出", ko: "출력") + ": \(String(format: "%.1f", model.creditsPerOutputK))",
                                            systemImage: "arrow.up.circle"
                                        )
                                    }
                                    .font(.caption2)
                                    .foregroundStyle(.tertiary)
                                }
                                Spacer()
                                if isSelected {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundStyle(BrandConfig.brand)
                                        .font(.title3)
                                }
                            }
                            .padding(14)
                            .background(
                                RoundedRectangle(cornerRadius: 12)
                                    .fill(isSelected ? BrandConfig.brand.opacity(0.06) : BrandConfig.cardBackground)
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(isSelected ? BrandConfig.brand.opacity(0.3) : BrandConfig.separator, lineWidth: 1)
                            )
                        }
                    }
                }
                .padding(.horizontal, 16).padding(.vertical, 12)
            }
            .background(BrandConfig.backgroundColor)
            .navigationTitle(lang.t("モデルを選択", en: "Select Model", zh: "选择模型", ko: "모델 선택"))
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private func tierColor(_ tier: String) -> Color {
        switch tier.lowercased() {
        case "premium": return .purple
        case "standard": return .blue
        case "economy", "budget": return .green
        default: return .secondary
        }
    }
}
