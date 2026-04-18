---
name: apple-notes
description: Create, read, and organize notes in Apple Notes via AppleScript or Shortcuts
version: 1.0.0
tags: [apple, notes, macos, ios, applescript, shortcuts]
category: apple
platform: macos
triggers: [Apple Notes, メモ, note, ノート, メモアプリ, create note, ノート作成, apple memo]
---

## 使用場面
Apple Notes へのメモ作成・読み取り、フォルダ整理、iCloud 同期されたメモの管理。

## AppleScript でノート操作

### ノートの作成
```applescript
tell application "Notes"
    tell account "iCloud"
        tell folder "仕事"
            make new note with properties {
                name: "ミーティングメモ 2024-01-15",
                body: "<b>アジェンダ</b><br>1. スプリントレビュー<br>2. 次週の計画"
            }
        end tell
    end tell
end tell
```

### ノートの検索・読み取り
```applescript
tell application "Notes"
    set matchingNotes to every note whose name contains "ミーティング"
    repeat with n in matchingNotes
        log (name of n) & ": " & (body of n)
    end repeat
end tell
```

### フォルダ一覧の取得
```applescript
tell application "Notes"
    tell account "iCloud"
        set folderNames to name of every folder
        return folderNames
    end tell
end tell
```

## Shell から実行
```bash
# AppleScript をシェルから実行
osascript -e 'tell application "Notes" to make new note with properties {name:"Test", body:"Hello"}'

# ファイルから実行
osascript create_note.applescript
```

## Shortcuts (ショートカット) での活用
```
アクション: "ノートを作成"
  ノート: [テキスト変数]
  フォルダ: 仕事
  アカウント: iCloud

アクション: "ノートを検索"
  フィルタ: タイトルに "会議" が含まれる
```

## ノート本文の HTML フォーマット
```html
<b>太字テキスト</b>
<i>斜体テキスト</i>
<br>改行
<ul><li>箇条書き</li></ul>
<h1>見出し</h1>
```

## 注意事項
- Apple Notes は macOS/iOS のみ対応
- iCloud 同期が有効な場合、全デバイスに反映
- プライベートノート（ロック）は AppleScript からアクセス不可

## 検証
Notes アプリを開いて、作成したノートが表示されれば完了。
