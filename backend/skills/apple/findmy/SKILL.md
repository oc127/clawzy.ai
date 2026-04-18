---
name: findmy
description: Interact with Apple Find My to locate devices and items via AppleScript
version: 1.0.0
tags: [apple, findmy, location, device, airtag, macos]
category: apple
platform: macos
triggers: [Find My, 探す, location, 位置情報, AirTag, device location, デバイス位置, 紛失]
---

## 使用場面
デバイスや AirTag の現在地確認、紛失デバイスへの音鳴らし、場所の確認通知。

## Find My の操作

### AppleScript で Find My アプリを開く
```applescript
tell application "Find My"
    activate
end tell
```

### デバイス情報の取得
```applescript
tell application "Find My"
    -- 全デバイス一覧
    set myDevices to devices
    repeat with d in myDevices
        log (name of d) & " - " & (status of d as string)
    end repeat
end tell
```

### 音を鳴らす（Play Sound）
```applescript
tell application "Find My"
    set targetDevice to first device whose name is "iPhone"
    play sound on targetDevice
end tell
```

### 紛失モードの有効化
```applescript
tell application "Find My"
    set targetDevice to first device whose name is "MacBook Pro"
    mark as lost targetDevice with message "紛失した場合は 090-xxxx-xxxx へ"
end tell
```

## Shell からの自動化
```bash
# Find My アプリを開いてデバイス一覧を表示
osascript -e 'tell application "Find My" to activate'

# Shortcuts と組み合わせて位置情報を取得
shortcuts run "デバイスの位置を確認"
```

## Shortcuts でのロケーション活用
```
トリガー: 毎朝 8 時
アクション 1: "デバイスを取得" (Find My)
アクション 2: "場所を取得" → デバイス.location
アクション 3: "メモを作成" → "MacBook の位置: [場所]"
```

## iCloud API アクセス（非公式）
```bash
# iCloud の Find My は Web API 経由でもアクセス可能（要認証）
# https://www.icloud.com/find
# 公式 API は提供されていないため AppleScript 推奨
```

## 注意事項
- Find My は Apple ID でのログインが必要
- 位置情報の精度はデバイスの種類による（GPS vs Wi-Fi）
- プライバシー法規を遵守すること（他人のデバイスを追跡しない）
- AirTag は Bluetooth 範囲 + クラウドリレーを使用

## 検証
Find My アプリでデバイスが地図上に表示されれば完了。
