---
name: arxiv
description: Search and retrieve academic papers from arXiv using the arXiv API
version: 1.0.0
tags: [arxiv, research, academic, papers, llm, ai]
category: research
platform: all
triggers: [arxiv, 論文, research paper, academic, 学術論文, AI論文, LLM paper, preprint]
---

## 使用場面
最新の AI/ML 論文の検索、特定分野の論文サーベイ、論文の要約取得、引用情報の確認。

## arXiv API での論文検索
```python
import httpx
import xml.etree.ElementTree as ET

BASE_URL = "http://export.arxiv.org/api/query"

def search_arxiv(query: str, max_results: int = 10, category: str = "cs.AI"):
    params = {
        "search_query": f"cat:{category} AND ({query})",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    resp = httpx.get(BASE_URL, params=params)
    return parse_arxiv_response(resp.text)

def parse_arxiv_response(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    
    papers = []
    for entry in root.findall("atom:entry", ns):
        papers.append({
            "id": entry.find("atom:id", ns).text.split("/")[-1],
            "title": entry.find("atom:title", ns).text.strip(),
            "summary": entry.find("atom:summary", ns).text.strip()[:500],
            "published": entry.find("atom:published", ns).text[:10],
            "authors": [a.find("atom:name", ns).text 
                       for a in entry.findall("atom:author", ns)],
            "url": entry.find("atom:id", ns).text,
        })
    return papers
```

## 使用例
```python
# LLM に関する最新論文を検索
papers = search_arxiv("large language model reasoning", max_results=5)

for p in papers:
    print(f"📄 {p['title']}")
    print(f"   著者: {', '.join(p['authors'][:3])}")
    print(f"   公開: {p['published']}")
    print(f"   URL: {p['url']}")
    print(f"   概要: {p['summary'][:200]}...")
    print()
```

## カテゴリ一覧（よく使うもの）
| カテゴリ | 分野 |
|---------|------|
| `cs.AI` | 人工知能 |
| `cs.LG` | 機械学習 |
| `cs.CL` | 計算言語学 (NLP) |
| `cs.CV` | コンピュータビジョン |
| `cs.RO` | ロボティクス |
| `stat.ML` | 統計的機械学習 |

## 特定 ID で論文を取得
```python
def get_paper(arxiv_id: str) -> dict:
    params = {"id_list": arxiv_id}
    resp = httpx.get(BASE_URL, params=params)
    papers = parse_arxiv_response(resp.text)
    return papers[0] if papers else None

paper = get_paper("2303.08774")  # GPT-4 技術レポート
```

## PDF のダウンロード
```python
def download_pdf(arxiv_id: str, save_path: str):
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    resp = httpx.get(pdf_url, follow_redirects=True)
    with open(save_path, "wb") as f:
        f.write(resp.content)
```

## 注意事項
- arXiv API は 3 秒に 1 リクエストの制限がある
- `arxiv` パッケージを使うとより簡単: `pip install arxiv`
- プレプリントは査読前のため内容の信頼性を確認する

## 検証
論文タイトル・著者・URL が正しく取得できれば完了。
