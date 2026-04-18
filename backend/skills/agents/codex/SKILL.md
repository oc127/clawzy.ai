---
name: codex
description: Use OpenAI Codex/GPT-4o for code generation, explanation, and transformation
version: 1.0.0
tags: [codex, openai, gpt4, code-generation, ai-coding]
category: agents
platform: all
triggers: [codex, GPT-4, OpenAI, コード生成, code generation, コード説明, 変換, transform code]
---

## 使用場面
OpenAI の GPT-4o/o3 モデルを使ったコード生成・説明・変換・最適化。

## 基本的な API 使用

### コード生成
```python
from openai import OpenAI

client = OpenAI()  # OPENAI_API_KEY 環境変数から自動取得

response = client.chat.completions.create(
    model="gpt-4o",  # または "o3", "gpt-4o-mini"
    messages=[
        {"role": "system", "content": "あなたは Python の専門家です。簡潔で実用的なコードを書いてください。"},
        {"role": "user", "content": "FastAPI で JWT 認証ミドルウェアを実装してください。"}
    ],
    max_tokens=2000,
    temperature=0.2  # コード生成には低めの temperature
)
code = response.choices[0].message.content
```

### コードの説明
```python
def explain_code(code: str, lang: str = "Python") -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": f"この {lang} コードを日本語で説明してください:\n\n```{lang.lower()}\n{code}\n```"
        }]
    )
    return response.choices[0].message.content
```

### コードの変換
```python
def transform_code(source: str, from_lang: str, to_lang: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": f"{from_lang} を {to_lang} に変換してください。機能は同じに保つこと:\n\n```\n{source}\n```"
        }]
    )
    return response.choices[0].message.content
```

### Function Calling でコード実行
```python
tools = [{
    "type": "function",
    "function": {
        "name": "run_code",
        "description": "Python コードを実行する",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "実行する Python コード"}
            },
            "required": ["code"]
        }
    }
}]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "フィボナッチ数列の最初の10項を計算して"}],
    tools=tools,
    tool_choice="auto"
)
```

## o3 モデル（推論特化）
```python
# 複雑なアルゴリズム問題
response = client.chat.completions.create(
    model="o3",
    messages=[{
        "role": "user",
        "content": "グラフの最短経路を求める Dijkstra アルゴリズムを実装し、時間計算量を解説してください"
    }],
    reasoning_effort="high"  # low, medium, high
)
```

## 注意事項
- `OPENAI_API_KEY` を環境変数で設定する
- temperature=0 〜 0.3 がコード生成に最適
- o3 は高コスト。通常のコード生成は gpt-4o で十分
- 生成されたコードは必ずレビュー・テストする

## 検証
API が `200 OK` を返し、コードが構文エラーなく実行できれば完了。
