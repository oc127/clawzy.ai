---
name: himalaya
description: Manage email via Himalaya CLI — read, send, and organize messages from terminal
version: 1.0.0
tags: [email, himalaya, cli, terminal, imap, smtp]
category: email
platform: all
triggers: [email, メール, himalaya, send email, メール送信, inbox, 受信箱, IMAP, SMTP]
---

## 使用場面
ターミナルからのメール送受信、メールの自動処理、スクリプトからのメール操作。

## Himalaya のインストールと設定
```bash
# インストール
brew install himalaya  # macOS
cargo install himalaya  # Cargo

# 設定ファイル
cat ~/.config/himalaya/config.toml
```

```toml
# ~/.config/himalaya/config.toml
[accounts.gmail]
email = "user@gmail.com"
display_name = "田中太郎"
default = true

backend.type = "imap"
backend.host = "imap.gmail.com"
backend.port = 993
backend.encryption = "tls"
backend.login = "user@gmail.com"
backend.passwd.cmd = "gpg --decrypt ~/.mail-passwd.gpg"

sender.type = "smtp"
sender.host = "smtp.gmail.com"
sender.port = 587
sender.encryption = "start-tls"
sender.login = "user@gmail.com"
sender.passwd.cmd = "gpg --decrypt ~/.mail-passwd.gpg"
```

## 基本操作
```bash
# 受信箱の一覧（最新 20 件）
himalaya list

# 特定のメール番号を読む
himalaya read 42

# 受信箱を検索
himalaya search "from:boss@example.com"

# 未読のみ表示
himalaya search "unseen"
```

## メールの送信
```bash
# テンプレートを作成して送信
himalaya write <<'EOF'
From: me@example.com
To: team@example.com
Subject: デプロイ完了のお知らせ

皆さん、

本日 15:00 に本番環境へのデプロイが完了しました。

以上、よろしくお願いします。
EOF

# 添付ファイル付き
himalaya write --attach report.pdf
```

## Python から Himalaya を呼び出す
```python
import subprocess
import json

def list_emails(account: str = "gmail", limit: int = 10) -> list[dict]:
    result = subprocess.run(
        ["himalaya", "--account", account, "--output", "json", "list"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def send_email(to: str, subject: str, body: str) -> bool:
    template = f"To: {to}\nSubject: {subject}\n\n{body}"
    result = subprocess.run(
        ["himalaya", "send"],
        input=template, text=True, capture_output=True
    )
    return result.returncode == 0

# 使用例
emails = list_emails(limit=5)
for email in emails:
    print(f"{email['date']} - {email['from']['name']}: {email['subject']}")
```

## フラグ操作
```bash
# 既読にする
himalaya flag add 42 seen

# 重要マーク
himalaya flag add 42 flagged

# フォルダに移動
himalaya move 42 "Archive"
```

## 注意事項
- Gmail の場合、「アプリパスワード」の使用を推奨（2FA 必須）
- パスワードは `gpg` で暗号化して保存
- IMAPサーバーによって接続設定が異なる

## 検証
`himalaya list` でメール一覧が表示されれば設定完了。
