---
name: llm-wiki
description: LLM knowledge base — key concepts, models, techniques, and benchmarks reference
version: 1.0.0
tags: [llm, ai, knowledge-base, reference, models]
category: research
platform: all
triggers: [LLM, 大規模言語モデル, transformer, attention, fine-tuning, ファインチューニング, RAG, prompt engineering, プロンプト]
---

## 主要モデル一覧（2025年時点）

| プロバイダ | モデル | 特徴 |
|-----------|--------|------|
| Anthropic | Claude Opus 4.7 | 最高品質、長文・推論 |
| Anthropic | Claude Sonnet 4.6 | バランス、コーディング |
| Anthropic | Claude Haiku 4.5 | 高速・低コスト |
| OpenAI | GPT-4o | マルチモーダル |
| OpenAI | o3 | 高度な推論 |
| Google | Gemini 2.0 Ultra | マルチモーダル |
| DeepSeek | DeepSeek-R1 | 推論特化 |
| Meta | Llama 3.3 70B | オープンソース |

## 主要技術概念

### RAG (Retrieval-Augmented Generation)
外部知識ベースから関連情報を検索し、LLM のコンテキストに注入する手法。
```
ユーザー質問 → ベクトル検索 → 関連チャンク取得 → LLM + コンテキスト → 回答
```

### Prompt Engineering テクニック
- **Chain-of-Thought (CoT)**: 「ステップバイステップで考えてください」
- **Few-shot**: 例を与えて形式を示す
- **System Prompt**: キャラクター・制約の設定
- **XML Tags**: `<thinking>`, `<answer>` でパートを分離
- **Constitutional AI**: 原則に従った自己修正

### Fine-tuning vs. RAG
| | Fine-tuning | RAG |
|--|-------------|-----|
| 用途 | 口調・形式の統一 | 最新情報・長文知識 |
| コスト | 高い（学習費用） | 低い（推論のみ） |
| 更新 | 再学習が必要 | インデックス更新のみ |

### Context Window
モデルが一度に処理できるトークン数。
- Claude: 200K tokens
- GPT-4: 128K tokens
- Gemini: 1M tokens

## ベンチマーク
| ベンチマーク | 測定内容 |
|-------------|---------|
| MMLU | 多分野の知識（57 科目） |
| HumanEval | コード生成能力 |
| GSM8K | 数学的推論 |
| MATH | 高度な数学 |
| GPQA | 専門家レベルの質問 |

## Token 計算の目安
- 英語: 約 4 文字 = 1 token
- 日本語: 約 1〜2 文字 = 1 token
- コード: 約 3〜4 文字 = 1 token

## 検証
LLM に関する質問に対して正確な情報が提供できれば完了。
