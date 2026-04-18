---
name: gif-search
description: Search and retrieve GIFs from Giphy and Tenor APIs
version: 1.0.0
tags: [gif, giphy, tenor, media, animation]
category: media
platform: all
triggers: [GIF, gif, giphy, tenor, アニメーション, 動画像, 画像検索, reaction gif]
---

## 使用場面
チャット・プレゼンへの GIF 追加、リアクション GIF の検索、アニメーション素材の取得。

## Giphy API での GIF 検索
```python
import httpx

GIPHY_API_KEY = "your_api_key"  # https://developers.giphy.com/

def search_giphy(query: str, limit: int = 5, rating: str = "g") -> list[dict]:
    """Giphy で GIF を検索"""
    resp = httpx.get("https://api.giphy.com/v1/gifs/search", params={
        "api_key": GIPHY_API_KEY,
        "q": query,
        "limit": limit,
        "rating": rating,  # g, pg, pg-13, r
        "lang": "ja",
    })
    
    gifs = []
    for item in resp.json()["data"]:
        gifs.append({
            "id": item["id"],
            "title": item["title"],
            "url": item["url"],
            "gif_url": item["images"]["original"]["url"],
            "thumbnail": item["images"]["fixed_width"]["url"],
            "width": item["images"]["original"]["width"],
            "height": item["images"]["original"]["height"],
        })
    return gifs

# 使用例
gifs = search_giphy("congratulations 祝い")
for g in gifs:
    print(f"タイトル: {g['title']}")
    print(f"GIF URL: {g['gif_url']}")
```

## Tenor API（Google）
```python
TENOR_API_KEY = "your_api_key"  # https://tenor.com/developer

def search_tenor(query: str, limit: int = 5) -> list[dict]:
    """Tenor で GIF を検索"""
    resp = httpx.get("https://tenor.googleapis.com/v2/search", params={
        "q": query,
        "key": TENOR_API_KEY,
        "limit": limit,
        "locale": "ja_JP",
        "media_filter": "gif",
    })
    
    gifs = []
    for result in resp.json()["results"]:
        media = result["media_formats"]
        gifs.append({
            "id": result["id"],
            "title": result["content_description"],
            "gif_url": media["gif"]["url"],
            "thumbnail": media["tinygif"]["url"],
        })
    return gifs
```

## GIF をダウンロード
```python
def download_gif(url: str, save_path: str) -> str:
    """GIF をローカルに保存"""
    resp = httpx.get(url, follow_redirects=True)
    with open(save_path, "wb") as f:
        f.write(resp.content)
    return save_path

# Markdown に埋め込む
def gif_to_markdown(gif_url: str, alt_text: str = "GIF") -> str:
    return f"![{alt_text}]({gif_url})"
```

## 注意事項
- Giphy/Tenor の無料プランは 1 日のリクエスト数に制限がある
- Giphy: 1000 req/day（開発者プラン）
- コンテンツの著作権は各 GIF の作者に帰属
- `rating="g"` を指定して安全なコンテンツのみ取得する

## 検証
GIF の URL が取得でき、ブラウザで表示できれば完了。
