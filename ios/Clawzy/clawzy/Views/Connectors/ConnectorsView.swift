import SwiftUI

// MARK: - Connector Status

enum ConnectorStatus {
    case disconnected, connecting, connected
}

// MARK: - Connector Model

struct Connector: Identifiable {
    let id: String
    let emoji: String
    let nameJa: String
    let nameEn: String
    let nameZh: String
    let nameKo: String
    let descJa: String
    let descEn: String
    let descZh: String
    let descKo: String
    var status: ConnectorStatus = .disconnected
}

// MARK: - ConnectorsView

struct ConnectorsView: View {
    @Environment(\.lang) var lang
    @State private var connectors: [Connector] = Self.defaultConnectors
    @State private var toastVisible = false
    @State private var showTelegramConfig = false
    @State private var showLineConfig = false

    private let columns = [GridItem(.flexible()), GridItem(.flexible())]

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                bannerView

                LazyVGrid(columns: columns, spacing: 16) {
                    ForEach($connectors) { $connector in
                        ConnectorCard(connector: $connector) {
                            switch connector.id {
                            case "telegram": showTelegramConfig = true
                            case "line":     showLineConfig = true
                            default:         showComingSoon()
                            }
                        }
                    }
                }
                .padding(.horizontal, 16)
            }
            .padding(.bottom, 32)
        }
        .navigationTitle(lang.t("コネクター", en: "Connectors", zh: "连接器", ko: "커넥터"))
        .navigationBarTitleDisplayMode(.large)
        .overlay(alignment: .top) {
            if toastVisible {
                ToastView(message: lang.t("近日公開予定", en: "Coming Soon", zh: "即将推出", ko: "출시 예정"))
                    .padding(.top, 8)
                    .transition(.move(edge: .top).combined(with: .opacity))
            }
        }
        .sheet(isPresented: $showTelegramConfig) {
            TelegramConfigSheet { success in
                if success {
                    updateConnectorStatus(id: "telegram", to: .connected)
                }
            }
        }
        .sheet(isPresented: $showLineConfig) {
            LineConfigSheet { success in
                if success {
                    updateConnectorStatus(id: "line", to: .connected)
                }
            }
        }
    }

    // MARK: - Banner

    private var bannerView: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "wifi")
                .foregroundStyle(.orange)
                .padding(.top, 2)

            Text(lang.t(
                "デバイスの接続を維持するため、常にスリープ解除の許可を有効にすることをお勧めします",
                en: "We recommend enabling wake permission to keep your device connection active.",
                zh: "建议启用唤醒权限以保持设备连接。",
                ko: "장치 연결 유지를 위해 절전 해제 권한을 활성화하는 것을 권장합니다."
            ))
            .font(.caption)
            .foregroundStyle(.primary)
            .fixedSize(horizontal: false, vertical: true)

            Spacer(minLength: 0)

            Button {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            } label: {
                Text(lang.t("設定へ", en: "Settings", zh: "去设置", ko: "설정으로"))
                    .font(.caption.bold())
                    .foregroundStyle(.orange)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.orange.opacity(0.12))
                    .clipShape(Capsule())
            }
        }
        .padding(12)
        .background(Color.orange.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .padding(.horizontal, 16)
        .padding(.top, 8)
    }

    // MARK: - Helpers

    private func showComingSoon() {
        guard !toastVisible else { return }
        withAnimation(.spring(response: 0.3)) {
            toastVisible = true
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            withAnimation(.spring(response: 0.3)) {
                toastVisible = false
            }
        }
    }

    private func updateConnectorStatus(id: String, to newStatus: ConnectorStatus) {
        if let idx = connectors.firstIndex(where: { $0.id == id }) {
            connectors[idx].status = newStatus
        }
    }

    // MARK: - Default Connectors

    static let defaultConnectors: [Connector] = [
        Connector(
            id: "line", emoji: "💬",
            nameJa: "LINE", nameEn: "LINE", nameZh: "LINE", nameKo: "LINE",
            descJa: "LINEと連携してAIアシスタントをLINEで使用",
            descEn: "Use AI assistant via LINE messaging",
            descZh: "通过LINE使用AI助手",
            descKo: "LINE으로 AI 어시스턴트 사용"
        ),
        Connector(
            id: "wechat", emoji: "🟢",
            nameJa: "WeChat", nameEn: "WeChat", nameZh: "微信", nameKo: "위챗",
            descJa: "WeChatと連携してAIアシスタントを使用",
            descEn: "Use AI assistant via WeChat",
            descZh: "通过微信使用AI助手",
            descKo: "위챗으로 AI 어시스턴트 사용"
        ),
        Connector(
            id: "telegram", emoji: "✈️",
            nameJa: "Telegram", nameEn: "Telegram", nameZh: "Telegram", nameKo: "텔레그램",
            descJa: "Telegramボットを簡単に接続",
            descEn: "Connect your Telegram bot easily",
            descZh: "轻松连接Telegram机器人",
            descKo: "텔레그램 봇을 쉽게 연결"
        ),
        Connector(
            id: "discord", emoji: "🎮",
            nameJa: "Discord", nameEn: "Discord", nameZh: "Discord", nameKo: "디스코드",
            descJa: "Discordサーバーにボットを追加",
            descEn: "Add a bot to your Discord server",
            descZh: "将机器人添加到Discord服务器",
            descKo: "Discord 서버에 봇 추가"
        ),
        Connector(
            id: "slack", emoji: "💼",
            nameJa: "Slack", nameEn: "Slack", nameZh: "Slack", nameKo: "슬랙",
            descJa: "Slackワークスペースに接続",
            descEn: "Connect to your Slack workspace",
            descZh: "连接到Slack工作区",
            descKo: "Slack 워크스페이스에 연결"
        ),
        Connector(
            id: "whatsapp", emoji: "📞",
            nameJa: "WhatsApp", nameEn: "WhatsApp", nameZh: "WhatsApp", nameKo: "왓츠앱",
            descJa: "WhatsAppでAIチャットを使用",
            descEn: "Use AI chat via WhatsApp",
            descZh: "通过WhatsApp使用AI聊天",
            descKo: "WhatsApp으로 AI 채팅 사용"
        ),
        Connector(
            id: "feishu", emoji: "🐦",
            nameJa: "飛書 (Lark)", nameEn: "Feishu / Lark", nameZh: "飞书", nameKo: "페이슈",
            descJa: "飛書（Lark）と連携",
            descEn: "Integrate with Feishu / Lark",
            descZh: "与飞书集成",
            descKo: "Feishu/Lark 연동"
        ),
        Connector(
            id: "dingtalk", emoji: "🔔",
            nameJa: "DingTalk (钉钉)", nameEn: "DingTalk", nameZh: "钉钉", nameKo: "딩톡",
            descJa: "钉钉（DingTalk）と連携",
            descEn: "Integrate with DingTalk",
            descZh: "与钉钉集成",
            descKo: "DingTalk 연동"
        ),
    ]
}

// MARK: - Connector Card

private struct ConnectorCard: View {
    @Binding var connector: Connector
    let onConnect: () -> Void
    @Environment(\.lang) var lang

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top) {
                Text(connector.emoji)
                    .font(.system(size: 34))
                Spacer()
                statusBadge
            }

            Text(lang.t(connector.nameJa, en: connector.nameEn, zh: connector.nameZh, ko: connector.nameKo))
                .font(.system(size: 15, weight: .semibold))
                .lineLimit(1)

            Text(lang.t(connector.descJa, en: connector.descEn, zh: connector.descZh, ko: connector.descKo))
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(3)
                .fixedSize(horizontal: false, vertical: true)

            Spacer(minLength: 4)

            Button(action: onConnect) {
                Text(connectButtonLabel)
                    .font(.caption.bold())
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(buttonBackground)
                    .foregroundStyle(buttonForeground)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .disabled(connector.status == .connecting)
        }
        .padding(14)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }

    @ViewBuilder
    private var statusBadge: some View {
        switch connector.status {
        case .disconnected:
            EmptyView()
        case .connecting:
            ProgressView()
                .scaleEffect(0.7)
        case .connected:
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(.green)
                .font(.system(size: 16))
        }
    }

    private var connectButtonLabel: String {
        switch connector.status {
        case .disconnected: return lang.t("接続する", en: "Connect", zh: "连接", ko: "연결")
        case .connecting:   return lang.t("接続中...", en: "Connecting...", zh: "连接中...", ko: "연결 중...")
        case .connected:    return lang.t("接続済み", en: "Connected", zh: "已连接", ko: "연결됨")
        }
    }

    private var buttonBackground: Color {
        switch connector.status {
        case .disconnected: return BrandConfig.brand
        case .connecting:   return BrandConfig.brand.opacity(0.6)
        case .connected:    return Color.green.opacity(0.15)
        }
    }

    private var buttonForeground: Color {
        switch connector.status {
        case .disconnected, .connecting: return .white
        case .connected:                 return .green
        }
    }
}

// MARK: - Connector API Response

private struct ConnectorValidateResponse: Decodable {
    let valid: Bool
    let detail: String
}

// MARK: - Telegram Config Sheet

struct TelegramConfigSheet: View {
    let onConnected: (Bool) -> Void

    @Environment(\.dismiss) private var dismiss
    @Environment(\.lang) private var lang

    @State private var botToken = ""
    @State private var isLoading = false
    @State private var statusMessage: String? = nil
    @State private var isSuccess = false

    private let steps: [(String, String, String, String)] = [
        ("1. Telegramを開き @BotFather を検索",
         "1. Open Telegram and search for @BotFather",
         "1. 打开Telegram，搜索 @BotFather",
         "1. Telegram을 열고 @BotFather를 검색하세요"),
        ("2. /newbot を送信して指示に従う",
         "2. Send /newbot and follow the instructions",
         "2. 发送 /newbot 并按照说明操作",
         "2. /newbot을 보내고 지시를 따르세요"),
        ("3. 提供されたボットトークンをコピー",
         "3. Copy the bot token provided",
         "3. 复制提供的机器人令牌",
         "3. 제공된 봇 토큰을 복사하세요"),
        ("4. 以下にトークンを貼り付け",
         "4. Paste the token below",
         "4. 将令牌粘贴到下方",
         "4. 아래에 토큰을 붙여넣으세요"),
    ]

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(steps, id: \.1) { step in
                            Text(lang.t(step.0, en: step.1, zh: step.2, ko: step.3))
                                .font(.callout)
                                .foregroundStyle(.primary)
                        }
                    }
                    .padding(.vertical, 4)

                    Link(lang.t("ガイドを見る", en: "View Guide", zh: "查看指南", ko: "가이드 보기"),
                         destination: URL(string: "https://core.telegram.org/bots#creating-a-new-bot")!)
                        .font(.callout)
                        .foregroundStyle(BrandConfig.brand)
                }

                Section(lang.t("ボットトークン", en: "Bot Token", zh: "机器人令牌", ko: "봇 토큰")) {
                    TextField(
                        lang.t("@BotFather からのトークンを入力", en: "Enter bot token from @BotFather",
                               zh: "输入来自 @BotFather 的令牌", ko: "@BotFather의 봇 토큰 입력"),
                        text: $botToken
                    )
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)
                }

                if let msg = statusMessage {
                    Section {
                        Label(msg, systemImage: isSuccess ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundStyle(isSuccess ? .green : .red)
                            .font(.callout)
                    }
                }

                Section {
                    Button {
                        Task { await validateToken() }
                    } label: {
                        HStack {
                            Text(lang.t("設定を検証", en: "Validate Config", zh: "验证配置", ko: "설정 확인"))
                            Spacer()
                            if isLoading { ProgressView().scaleEffect(0.8) }
                        }
                    }
                    .disabled(botToken.trimmingCharacters(in: .whitespaces).isEmpty || isLoading)

                    Button {
                        Task { await connectBot() }
                    } label: {
                        Text(lang.t("保存して接続", en: "Save & Connect", zh: "保存并连接", ko: "저장 및 연결"))
                            .bold()
                            .frame(maxWidth: .infinity)
                    }
                    .disabled(botToken.trimmingCharacters(in: .whitespaces).isEmpty || isLoading)
                }
            }
            .navigationTitle(lang.t("Telegramを設定", en: "Configure Telegram",
                                    zh: "配置Telegram", ko: "Telegram 설정"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소")) { dismiss() }
                }
            }
        }
    }

    private func validateToken() async {
        isLoading = true
        statusMessage = nil
        defer { isLoading = false }

        let token = botToken.trimmingCharacters(in: .whitespaces)
        do {
            let resp: ConnectorValidateResponse = try await APIClient.shared.request(
                Constants.API.connectorsValidateTelegram,
                method: "POST",
                body: ["bot_token": token]
            )
            isSuccess = resp.valid
            statusMessage = resp.detail
        } catch {
            isSuccess = false
            statusMessage = error.localizedDescription
        }
    }

    private func connectBot() async {
        isLoading = true
        statusMessage = nil
        defer { isLoading = false }

        let token = botToken.trimmingCharacters(in: .whitespaces)
        do {
            let resp: ConnectorValidateResponse = try await APIClient.shared.request(
                Constants.API.connectorsConnectTelegram,
                method: "POST",
                body: ["bot_token": token]
            )
            isSuccess = resp.valid
            statusMessage = resp.detail
            if resp.valid {
                try? await Task.sleep(nanoseconds: 800_000_000)
                onConnected(true)
                dismiss()
            }
        } catch {
            isSuccess = false
            statusMessage = error.localizedDescription
        }
    }
}

// MARK: - LINE Config Sheet

struct LineConfigSheet: View {
    let onConnected: (Bool) -> Void

    @Environment(\.dismiss) private var dismiss
    @Environment(\.lang) private var lang

    @State private var channelAccessToken = ""
    @State private var channelSecret = ""
    @State private var webhookPath = "/webhooks/line"
    @State private var isLoading = false
    @State private var statusMessage: String? = nil
    @State private var isSuccess = false

    private let steps: [(String, String, String, String)] = [
        ("1. LINE Developers ConsoleでMessaging APIチャンネルを作成",
         "1. Create a Messaging API channel in the LINE Developers Console",
         "1. 在LINE Developers Console中创建Messaging API频道",
         "1. LINE Developers Console에서 Messaging API 채널을 생성하세요"),
        ("2. チャンネルシークレットとアクセストークンを取得",
         "2. Obtain the Channel Secret and Access Token",
         "2. 获取Channel Secret和Access Token",
         "2. Channel Secret과 Access Token을 획득하세요"),
        ("3. Webhook機能を有効にしてURLを貼り付け",
         "3. Enable Webhook functionality and paste the URL below",
         "3. 启用Webhook功能并将URL粘贴到下方",
         "3. Webhook 기능을 활성화하고 URL을 아래에 붙여넣으세요"),
    ]

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(steps, id: \.1) { step in
                            Text(lang.t(step.0, en: step.1, zh: step.2, ko: step.3))
                                .font(.callout)
                                .foregroundStyle(.primary)
                        }
                    }
                    .padding(.vertical, 4)

                    Link(lang.t("ガイドを見る", en: "View Guide", zh: "查看指南", ko: "가이드 보기"),
                         destination: URL(string: "https://developers.line.biz/en/docs/messaging-api/getting-started/")!)
                        .font(.callout)
                        .foregroundStyle(BrandConfig.brand)
                }

                Section(lang.t("チャンネル設定", en: "Channel Settings", zh: "频道设置", ko: "채널 설정")) {
                    TextField(
                        lang.t("チャンネルアクセストークン", en: "Channel Access Token",
                               zh: "Channel Access Token", ko: "채널 액세스 토큰"),
                        text: $channelAccessToken
                    )
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)

                    TextField(
                        lang.t("チャンネルシークレット", en: "Channel Secret",
                               zh: "Channel Secret", ko: "채널 시크릿"),
                        text: $channelSecret
                    )
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)

                    TextField(
                        lang.t("Webhookパス", en: "Webhook Path",
                               zh: "Webhook路径", ko: "Webhook 경로"),
                        text: $webhookPath
                    )
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)
                }

                if let msg = statusMessage {
                    Section {
                        Label(msg, systemImage: isSuccess ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundStyle(isSuccess ? .green : .red)
                            .font(.callout)
                    }
                }

                Section {
                    Button {
                        Task { await validateToken() }
                    } label: {
                        HStack {
                            Text(lang.t("設定を検証", en: "Validate Config", zh: "验证配置", ko: "설정 확인"))
                            Spacer()
                            if isLoading { ProgressView().scaleEffect(0.8) }
                        }
                    }
                    .disabled(channelAccessToken.trimmingCharacters(in: .whitespaces).isEmpty || isLoading)

                    Button {
                        Task { await connectChannel() }
                    } label: {
                        Text(lang.t("保存して接続", en: "Save & Connect", zh: "保存并连接", ko: "저장 및 연결"))
                            .bold()
                            .frame(maxWidth: .infinity)
                    }
                    .disabled(
                        channelAccessToken.trimmingCharacters(in: .whitespaces).isEmpty ||
                        channelSecret.trimmingCharacters(in: .whitespaces).isEmpty ||
                        isLoading
                    )
                }
            }
            .navigationTitle(lang.t("LINEを設定", en: "Configure LINE", zh: "配置LINE", ko: "LINE 설정"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소")) { dismiss() }
                }
            }
        }
    }

    private func validateToken() async {
        isLoading = true
        statusMessage = nil
        defer { isLoading = false }

        let token = channelAccessToken.trimmingCharacters(in: .whitespaces)
        do {
            let resp: ConnectorValidateResponse = try await APIClient.shared.request(
                Constants.API.connectorsValidateLine,
                method: "POST",
                body: ["channel_access_token": token]
            )
            isSuccess = resp.valid
            statusMessage = resp.detail
        } catch {
            isSuccess = false
            statusMessage = error.localizedDescription
        }
    }

    private func connectChannel() async {
        isLoading = true
        statusMessage = nil
        defer { isLoading = false }

        struct LineConnectBody: Encodable {
            let channel_access_token: String
            let channel_secret: String
            let webhook_path: String
        }

        let body = LineConnectBody(
            channel_access_token: channelAccessToken.trimmingCharacters(in: .whitespaces),
            channel_secret: channelSecret.trimmingCharacters(in: .whitespaces),
            webhook_path: webhookPath.trimmingCharacters(in: .whitespaces)
        )

        do {
            let resp: ConnectorValidateResponse = try await APIClient.shared.request(
                Constants.API.connectorsConnectLine,
                method: "POST",
                body: body
            )
            isSuccess = resp.valid
            statusMessage = resp.detail
            if resp.valid {
                try? await Task.sleep(nanoseconds: 800_000_000)
                onConnected(true)
                dismiss()
            }
        } catch {
            isSuccess = false
            statusMessage = error.localizedDescription
        }
    }
}

// MARK: - Toast

private struct ToastView: View {
    let message: String

    var body: some View {
        Text(message)
            .font(.subheadline.bold())
            .foregroundStyle(.white)
            .padding(.horizontal, 20)
            .padding(.vertical, 10)
            .background(Color.black.opacity(0.8))
            .clipShape(Capsule())
    }
}
