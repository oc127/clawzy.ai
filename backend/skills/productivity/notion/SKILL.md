---
name: notion
description: Read and write Notion pages, databases, and blocks via Notion API
version: 1.0.0
tags: [notion, database, page, wiki, documentation]
category: productivity
platform: all
triggers: [notion, ノーション, Notion page, データベース, wiki, ドキュメント管理, notion api]
---

## 使用場面
Notion データベースへのレコード追加、ページの作成・更新、コンテンツの読み取り、ドキュメント管理の自動化。

## 認証設定
```python
from notion_client import Client

notion = Client(auth="secret_xxxxxxxxxxxx")
DATABASE_ID = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

## データベースにレコードを追加
```python
notion.pages.create(
    parent={"database_id": DATABASE_ID},
    properties={
        "タイトル": {"title": [{"text": {"content": "新しいタスク"}}]},
        "ステータス": {"select": {"name": "進行中"}},
        "担当者": {"people": [{"id": "USER_ID"}]},
        "期日": {"date": {"start": "2024-01-20"}},
        "優先度": {"select": {"name": "高"}},
    }
)
```

## データベースのクエリ
```python
# フィルタと並び替えで検索
response = notion.databases.query(
    database_id=DATABASE_ID,
    filter={
        "and": [
            {"property": "ステータス", "select": {"equals": "進行中"}},
            {"property": "期日", "date": {"on_or_before": "2024-01-31"}},
        ]
    },
    sorts=[{"property": "期日", "direction": "ascending"}]
)
results = response["results"]
```

## ページの作成
```python
page = notion.pages.create(
    parent={"page_id": "PARENT_PAGE_ID"},
    properties={"title": {"title": [{"text": {"content": "月次レポート"}}]}},
    children=[
        {"object": "block", "type": "heading_1",
         "heading_1": {"rich_text": [{"text": {"content": "概要"}}]}},
        {"object": "block", "type": "paragraph",
         "paragraph": {"rich_text": [{"text": {"content": "今月の成果..."}}]}},
        {"object": "block", "type": "bulleted_list_item",
         "bulleted_list_item": {"rich_text": [{"text": {"content": "✅ 機能A をリリース"}}]}},
    ]
)
```

## ページ内容の読み取り
```python
# ブロック一覧を取得
blocks = notion.blocks.children.list(block_id="PAGE_ID")
for block in blocks["results"]:
    if block["type"] == "paragraph":
        texts = block["paragraph"]["rich_text"]
        print("".join(t["plain_text"] for t in texts))
```

## ページの更新
```python
# プロパティを更新
notion.pages.update(
    page_id="PAGE_ID",
    properties={
        "ステータス": {"select": {"name": "完了"}},
    }
)
```

## 注意事項
- インテグレーションは対象のページ/DBで共有設定が必要
- `notion-client` パッケージをインストール: `pip install notion-client`
- レート制限: 3 req/sec

## 検証
Notion のデータベースでレコードが追加されれば完了。
