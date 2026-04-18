---
name: google-workspace
description: Automate Google Docs, Sheets, Gmail, and Drive via Google API
version: 1.0.0
tags: [google, docs, sheets, gmail, drive, workspace, api]
category: productivity
platform: all
triggers: [Google Docs, Google Sheets, Gmail, Google Drive, スプレッドシート, ドキュメント, ドライブ, google api]
---

## 使用場面
Google Sheets へのデータ書き込み、Docs のコンテンツ生成、Gmail の自動送信、Drive のファイル管理。

## 認証設定
```python
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/gmail.send',
]
creds = Credentials.from_service_account_file('service-account.json', scopes=SCOPES)
```

## Google Sheets
```python
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# データを書き込む
sheet.values().update(
    spreadsheetId='SPREADSHEET_ID',
    range='Sheet1!A1:C3',
    valueInputOption='RAW',
    body={'values': [
        ['名前', '売上', '日付'],
        ['田中', 100000, '2024-01-15'],
    ]}
).execute()

# データを読み取る
result = sheet.values().get(
    spreadsheetId='SPREADSHEET_ID',
    range='Sheet1!A1:Z100'
).execute()
rows = result.get('values', [])
```

## Google Docs
```python
service = build('docs', 'v1', credentials=creds)

# 新しいドキュメント作成
doc = service.documents().create(body={'title': '月次レポート'}).execute()
doc_id = doc['documentId']

# テキストを追加
service.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': [{
        'insertText': {
            'location': {'index': 1},
            'text': '# 月次レポート\n\n本文テキスト...'
        }
    }]}
).execute()
```

## Gmail
```python
import base64
from email.mime.text import MIMEText
service = build('gmail', 'v1', credentials=creds)

message = MIMEText('メール本文')
message['to'] = 'recipient@example.com'
message['subject'] = '月次レポートのお知らせ'

raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
service.users().messages().send(
    userId='me',
    body={'raw': raw}
).execute()
```

## 注意事項
- サービスアカウントは共有されたファイルのみアクセス可能
- Gmail は `gmail.send` スコープで送信専用アクセスを使う
- API クォータ制限に注意（Sheets: 300 req/min）

## 検証
Sheets のデータが更新され、Docs ファイルが作成されれば完了。
