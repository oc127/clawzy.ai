---
name: imessage
description: Send messages and read conversations via Apple Messages using AppleScript
version: 1.0.0
tags: [imessage, messages, apple, sms, macos, applescript]
category: apple
platform: macos
triggers: [iMessage, Messages, メッセージ, SMS, send message, メッセージ送信, 連絡先, contact]
---

## 使用場面
自動メッセージ送信、会話の読み取り、グループチャットへの投稿、通知の処理。

## AppleScript でメッセージ操作

### メッセージの送信
```applescript
tell application "Messages"
    set targetBuddy to buddy "09012345678" of service "SMS"
    -- または iMessage
    set targetBuddy to buddy "user@example.com" of service "iMessage"
    
    send "こんにちは！ミーティングは 3 時からです。" to targetBuddy
end tell
```

### 最新のメッセージを取得
```applescript
tell application "Messages"
    set recentChats to chats
    set firstChat to item 1 of recentChats
    
    tell firstChat
        set recentMessages to messages
        set lastMsg to item -1 of recentMessages
        return {body of lastMsg, date of lastMsg}
    end tell
end tell
```

### グループチャットへの送信
```applescript
tell application "Messages"
    -- グループチャット名で検索
    set groupChat to first chat whose name is "開発チーム"
    send "デプロイ完了しました ✅" to groupChat
end tell
```

### 既読確認
```applescript
tell application "Messages"
    -- 未読メッセージ数
    set unreadCount to count (chats whose has unread messages is true)
    return unreadCount
end tell
```

## Shell から実行
```bash
# 簡単なメッセージ送信
osascript -e 'tell application "Messages" to send "テスト" to buddy "09012345678" of service "SMS"'
```

## ファイル送信
```applescript
tell application "Messages"
    set targetBuddy to buddy "user@example.com" of service "iMessage"
    send POSIX file "/Users/user/Desktop/report.pdf" to targetBuddy
end tell
```

## 注意事項
- macOS の「フルディスクアクセス」権限が必要な場合がある
- 電話番号は国際形式も使用可能（+81901234567）
- iMessage と SMS は別サービスとして扱われる
- プライバシー設定によりアクセスが制限される場合がある

## 検証
Messages アプリで送信済みメッセージが確認できれば完了。
