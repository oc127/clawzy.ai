---
name: apple-reminders
description: Create and manage reminders in Apple Reminders via AppleScript
version: 1.0.0
tags: [apple, reminders, task, todo, macos, ios]
category: apple
platform: macos
triggers: [リマインダー, reminder, Apple Reminders, タスク追加, todo, 期日, due date, アラーム, alarm]
---

## 使用場面
リマインダーの作成・管理、期日設定、リスト整理、定期タスクの設定。

## AppleScript でリマインダー操作

### リマインダーの作成
```applescript
tell application "Reminders"
    tell list "仕事"
        set newReminder to make new reminder with properties {
            name: "スプリントレビュー資料を準備",
            due date: date "2024/01/20 10:00:00",
            remind me date: date "2024/01/19 18:00:00",
            body: "スライド20枚、デモ環境の確認"
        }
    end tell
end tell
```

### 今日のリマインダーを取得
```applescript
tell application "Reminders"
    set todayStart to current date
    set hours of todayStart to 0
    set minutes of todayStart to 0
    set seconds of todayStart to 0
    
    set todayEnd to todayStart + 1 * days
    
    set todayItems to reminders whose due date >= todayStart and due date < todayEnd
    return name of todayItems
end tell
```

### リマインダーの完了
```applescript
tell application "Reminders"
    set targetReminder to first reminder whose name is "スプリントレビュー資料を準備"
    set completed of targetReminder to true
end tell
```

### リスト一覧の取得
```applescript
tell application "Reminders"
    set listNames to name of every list
    return listNames
end tell
```

## Shell から実行
```bash
# 明日の 9 時にリマインダーを作成
osascript <<'EOF'
tell application "Reminders"
    tell list "個人"
        make new reminder with properties {
            name: "薬を飲む",
            due date: (current date) + 1 * days
        }
    end tell
end tell
EOF
```

## 優先度設定
```applescript
-- priority: 0=なし, 1=高, 5=中, 9=低
set priority of newReminder to 1
```

## 注意事項
- Reminders は macOS 10.15+ と iOS 13+ で対応
- iCloud リマインダーはデバイス間で同期
- プライベートリストは AppleScript からアクセス不可

## 検証
Reminders アプリでリマインダーが表示されれば完了。
