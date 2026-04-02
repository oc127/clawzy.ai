import SwiftUI

struct ChannelsView: View {
    let agentId: String
    @State private var service = AgentDetailService()
    @State private var showAddChannel = false
    @Environment(\.lang) var lang

    private func channelIcon(_ type: String) -> String {
        switch type.lowercased() {
        case "telegram": return "paperplane.fill"
        case "line":     return "message.fill"
        default:         return "bubble.left.fill"
        }
    }

    private func channelColor(_ type: String) -> Color {
        switch type.lowercased() {
        case "telegram": return .blue
        case "line":     return .green
        default:         return BrandConfig.brand
        }
    }

    var body: some View {
        Group {
            if service.isLoading && service.channels.isEmpty {
                ProgressView(lang.t("読み込み中...", en: "Loading...", zh: "加载中...", ko: "로딩 중..."))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if service.channels.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "bubble.left.and.bubble.right")
                        .font(.largeTitle)
                        .foregroundStyle(.secondary)
                    Text(lang.t("チャンネルがありません", en: "No channels connected", zh: "暂无频道", ko: "연결된 채널이 없습니다"))
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List {
                    ForEach(service.channels) { channel in
                        HStack(spacing: 12) {
                            ZStack {
                                Circle()
                                    .fill(channelColor(channel.type).opacity(0.15))
                                    .frame(width: 40, height: 40)
                                Image(systemName: channelIcon(channel.type))
                                    .foregroundStyle(channelColor(channel.type))
                            }
                            VStack(alignment: .leading, spacing: 4) {
                                Text(channel.type.capitalized)
                                    .font(.subheadline).fontWeight(.medium)
                                if let status = channel.status {
                                    Text(status)
                                        .font(.caption)
                                        .foregroundStyle(status == "active" ? .green : .secondary)
                                }
                            }
                            Spacer()
                            if let config = channel.config {
                                VStack(alignment: .trailing, spacing: 2) {
                                    ForEach(Array(config.keys.sorted().prefix(2)), id: \.self) { key in
                                        Text("\(key)")
                                            .font(.caption2)
                                            .foregroundStyle(.tertiary)
                                    }
                                }
                            }
                        }
                        .padding(.vertical, 4)
                    }
                    .onDelete { indexSet in
                        let toDelete = indexSet.map { service.channels[$0] }
                        for channel in toDelete {
                            Task {
                                await service.deleteChannel(agentId: agentId, channelId: channel.id)
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle(lang.t("チャンネル", en: "Channels", zh: "频道", ko: "채널"))
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    showAddChannel = true
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .foregroundStyle(BrandConfig.brand)
                }
            }
        }
        .sheet(isPresented: $showAddChannel) {
            AddChannelSheet(agentId: agentId, service: service) {
                showAddChannel = false
            }
        }
        .task { await service.fetchChannels(agentId: agentId) }
        .refreshable { await service.fetchChannels(agentId: agentId) }
    }
}

// MARK: - Add Channel Sheet

private struct AddChannelSheet: View {
    let agentId: String
    let service: AgentDetailService
    let onDismiss: () -> Void

    @State private var channelType = "telegram"
    @State private var botToken = ""
    @State private var chatId = ""
    @State private var channelToken = ""
    @State private var channelSecret = ""
    @State private var isSaving = false
    @Environment(\.lang) var lang
    @Environment(\.dismiss) var dismiss

    private let channelTypes = ["telegram", "line"]

    var isValid: Bool {
        if channelType == "telegram" {
            return !botToken.trimmingCharacters(in: .whitespaces).isEmpty
        } else {
            return !channelToken.trimmingCharacters(in: .whitespaces).isEmpty &&
                   !channelSecret.trimmingCharacters(in: .whitespaces).isEmpty
        }
    }

    var body: some View {
        NavigationStack {
            Form {
                Section(header: Text(lang.t("種類", en: "Type", zh: "类型", ko: "유형"))) {
                    Picker(lang.t("チャンネル", en: "Channel", zh: "频道", ko: "채널"), selection: $channelType) {
                        Text("Telegram").tag("telegram")
                        Text("LINE").tag("line")
                    }
                    .pickerStyle(.segmented)
                }

                if channelType == "telegram" {
                    Section(header: Text("Telegram")) {
                        LabeledField(label: lang.t("ボットトークン", en: "Bot Token", zh: "机器人令牌", ko: "봇 토큰")) {
                            TextField("123456:ABC-DEF...", text: $botToken)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                        }
                        LabeledField(label: lang.t("チャットID (任意)", en: "Chat ID (optional)", zh: "聊天ID（可选）", ko: "채팅 ID (선택)")) {
                            TextField("-100123456789", text: $chatId)
                                .textInputAutocapitalization(.never)
                                .keyboardType(.numbersAndPunctuation)
                        }
                    }
                } else {
                    Section(header: Text("LINE")) {
                        LabeledField(label: lang.t("チャンネルトークン", en: "Channel Token", zh: "频道令牌", ko: "채널 토큰")) {
                            TextField("Token", text: $channelToken)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                        }
                        LabeledField(label: lang.t("チャンネルシークレット", en: "Channel Secret", zh: "频道密钥", ko: "채널 시크릿")) {
                            TextField("Secret", text: $channelSecret)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                        }
                    }
                }
            }
            .navigationTitle(lang.t("チャンネル追加", en: "Add Channel", zh: "添加频道", ko: "채널 추가"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(lang.t("キャンセル", en: "Cancel", zh: "取消", ko: "취소")) { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button {
                        Task {
                            isSaving = true
                            var config: [String: String] = [:]
                            if channelType == "telegram" {
                                config["bot_token"] = botToken.trimmingCharacters(in: .whitespaces)
                                if !chatId.isEmpty {
                                    config["chat_id"] = chatId.trimmingCharacters(in: .whitespaces)
                                }
                            } else {
                                config["channel_token"] = channelToken.trimmingCharacters(in: .whitespaces)
                                config["channel_secret"] = channelSecret.trimmingCharacters(in: .whitespaces)
                            }
                            await service.createChannel(agentId: agentId, type: channelType, config: config)
                            isSaving = false
                            onDismiss()
                        }
                    } label: {
                        if isSaving { ProgressView() }
                        else { Text(lang.t("保存", en: "Save", zh: "保存", ko: "저장")) }
                    }
                    .disabled(!isValid || isSaving)
                }
            }
        }
        .presentationDetents([.medium, .large])
    }
}
