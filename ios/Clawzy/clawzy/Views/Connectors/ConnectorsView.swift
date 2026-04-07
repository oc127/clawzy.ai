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

    private let columns = [GridItem(.flexible()), GridItem(.flexible())]

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                bannerView

                LazyVGrid(columns: columns, spacing: 16) {
                    ForEach($connectors) { $connector in
                        ConnectorCard(connector: $connector) {
                            showComingSoon()
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

    // MARK: - Toast

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
