---
name: blogwatcher
description: Monitor RSS feeds and blogs for new content and aggregate updates
version: 1.0.0
tags: [rss, blog, monitor, feed, news, aggregation]
category: research
platform: all
triggers: [RSS, ブログ監視, feed, blog, ニュース収集, モニタリング, news aggregation, 最新情報]
---

## 使用場面
技術ブログの新着記事モニタリング、RSS フィードの集約、特定トピックのニュース収集。

## RSS フィード取得
```python
import feedparser
import httpx
from datetime import datetime

# pip install feedparser

def fetch_feed(url: str, max_items: int = 10) -> list[dict]:
    feed = feedparser.parse(url)
    items = []
    
    for entry in feed.entries[:max_items]:
        items.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", "")[:300],
            "published": entry.get("published", ""),
            "author": entry.get("author", ""),
        })
    return items
```

## 複数フィードの並列取得
```python
import asyncio
import aiohttp

TECH_FEEDS = {
    "Anthropic Blog": "https://www.anthropic.com/rss.xml",
    "OpenAI Blog": "https://openai.com/blog/rss.xml",
    "Google AI Blog": "https://blog.research.google/feeds/posts/default",
    "Hacker News Top": "https://hnrss.org/frontpage",
    "Zenn AI": "https://zenn.dev/topics/ai/feed",
}

async def fetch_all_feeds(feeds: dict[str, str]) -> dict[str, list]:
    async def fetch_one(name: str, url: str):
        return name, fetch_feed(url, max_items=5)
    
    tasks = [fetch_one(name, url) for name, url in feeds.items()]
    results = await asyncio.gather(*[asyncio.create_task(t) for t in tasks])
    return dict(results)

# 実行
updates = asyncio.run(fetch_all_feeds(TECH_FEEDS))
for source, articles in updates.items():
    print(f"\n📰 {source}")
    for a in articles:
        print(f"  - {a['title']}")
        print(f"    {a['link']}")
```

## キーワードフィルタリング
```python
def filter_by_keywords(items: list[dict], keywords: list[str]) -> list[dict]:
    matched = []
    kw_lower = [kw.lower() for kw in keywords]
    
    for item in items:
        text = (item["title"] + " " + item["summary"]).lower()
        if any(kw in text for kw in kw_lower):
            matched.append(item)
    return matched

# AI 関連の記事だけ抽出
ai_articles = filter_by_keywords(items, ["llm", "gpt", "claude", "gemini", "AI", "機械学習"])
```

## 新着チェック（差分検出）
```python
import json
from pathlib import Path

def get_new_articles(feed_url: str, seen_file: str = "seen.json") -> list[dict]:
    seen = set(json.loads(Path(seen_file).read_text())) if Path(seen_file).exists() else set()
    
    items = fetch_feed(feed_url)
    new_items = [i for i in items if i["link"] not in seen]
    
    seen.update(i["link"] for i in items)
    Path(seen_file).write_text(json.dumps(list(seen)))
    
    return new_items
```

## 注意事項
- RSS を提供しないサイトは `requests` + `BeautifulSoup` でスクレイピング
- 取得間隔は最低 1 時間（礼儀）
- Atom と RSS 2.0 は `feedparser` が自動識別する

## 検証
フィードから記事一覧が取得でき、キーワードフィルタが動作すれば完了。
