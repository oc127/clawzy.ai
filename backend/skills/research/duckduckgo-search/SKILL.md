---
name: duckduckgo-search
description: Search the web using DuckDuckGo API without API keys or tracking
version: 1.0.0
tags: [search, web, duckduckgo, ddg, research]
category: research
platform: all
triggers: [search, 検索, web search, ウェブ検索, duckduckgo, DDG, find information, 調べる]
---

## 使用場面
プライバシーを保ちつつウェブ検索、ニュース・画像の検索、API キー不要の簡単な検索。

## DuckDuckGo API 検索
```python
from duckduckgo_search import DDGS

# インストール
# pip install duckduckgo-search

ddgs = DDGS()

# テキスト検索
results = list(ddgs.text(
    "Python async best practices 2024",
    region="jp-jp",   # 日本語結果
    safesearch="off",
    timelimit="m",    # past month: d=day, w=week, m=month, y=year
    max_results=10
))

for r in results:
    print(f"タイトル: {r['title']}")
    print(f"URL: {r['href']}")
    print(f"概要: {r['body'][:200]}")
    print()
```

## ニュース検索
```python
news = list(ddgs.news(
    "AI 規制 日本 2024",
    region="jp-jp",
    timelimit="w",
    max_results=5
))

for n in news:
    print(f"📰 {n['title']}")
    print(f"   ソース: {n['source']}")
    print(f"   日付: {n['date']}")
    print(f"   URL: {n['url']}")
```

## 画像検索
```python
images = list(ddgs.images(
    "機械学習 アーキテクチャ 図",
    region="jp-jp",
    safesearch="off",
    type_image="photo",
    max_results=5
))

for img in images:
    print(f"画像 URL: {img['image']}")
    print(f"サムネイル: {img['thumbnail']}")
    print(f"ソース: {img['url']}")
```

## インスタントアンサー（DuckDuckGo ゼロクリック）
```python
import httpx

def ddg_instant(query: str) -> dict:
    """Wikipedia 要約や定義など短い答えを取得"""
    resp = httpx.get("https://api.duckduckgo.com/", params={
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
    })
    data = resp.json()
    return {
        "abstract": data.get("Abstract", ""),
        "source": data.get("AbstractSource", ""),
        "url": data.get("AbstractURL", ""),
        "answer": data.get("Answer", ""),
    }

result = ddg_instant("Python programming language")
```

## 非同期で並列検索
```python
import asyncio
from duckduckgo_search import AsyncDDGS

async def parallel_search(queries: list[str]):
    async with AsyncDDGS() as ddgs:
        tasks = [ddgs.atext(q, max_results=5) for q in queries]
        results = await asyncio.gather(*tasks)
    return results
```

## 注意事項
- API キー不要、完全無料
- IP ベースのレート制限あり（1 秒に複数リクエストは避ける）
- 日本語検索は `region="jp-jp"` を指定する

## 検証
検索結果のタイトル・URL・概要が返れば完了。
