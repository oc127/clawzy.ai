---
name: subagent-driven-development
description: Decompose complex tasks into parallel sub-agent workstreams for faster delivery
version: 1.0.0
tags: [subagent, parallel, orchestration, multi-agent, decompose]
category: software-dev
platform: all
triggers: [subagent, parallel, サブエージェント, 並列, decompose, split task, 分割, orchestrate, 並行]
---

## 使用場面
大規模なコードベース変更、独立した複数ファイルの同時修正、調査と実装を並行させる場面。

## サブエージェント分解の原則

### 1. 依存関係の分析
```
タスク分析:
  独立: A, B, C → 並列実行可能
  依存: D は A の完了後 → シリアル実行
  
実行順序:
  Round 1: A || B || C  (並列)
  Round 2: D           (直列)
```

### 2. サブエージェントへの指示原則
- **完全に自己完結した指示**：前の会話を知らない前提で書く
- **ファイルパスを明示**：`/absolute/path/to/file.py`
- **期待する出力形式**を指定
- **何を変更してはいけないか**も明示する

### 3. 効果的な分解パターン

**調査 + 実装の並列化**
```
Agent 1 (調査): 既存のパターン・APIを調査 → レポート
Agent 2 (実装): 既知の仕様でモデル実装
Agent 3 (テスト): テストケース設計
```

**レイヤー別の並列化**
```
Agent 1: DB モデル + マイグレーション
Agent 2: API エンドポイント（モックDBで）
Agent 3: フロントエンドコンポーネント
```

**コンポーネント別の並列化**
```
Agent 1: 認証モジュール
Agent 2: 通知モジュール
Agent 3: ファイル処理モジュール
```

## オーケストレーターの責務
1. タスクを独立した単位に分解する
2. 各エージェントへ完全な文脈を渡す
3. 結果を統合し、競合を解決する
4. 最終的な整合性を確認する

## 統合チェックリスト
```
□ 各エージェントの変更がコンフリクトしていないか
□ インターフェース（型・API）が一致しているか
□ テストが全体的に通るか
□ 命名規則が統一されているか
```

## 注意事項
- 過度な分解は統合コストが増える。3〜5 エージェントが最適
- 共有状態（DB・ファイル）にアクセスするタスクは並列化を避ける
- 不完全な結果のエージェントには再試行指示を出す

## 検証
全エージェントの結果を統合後、テストスイートが通れば完了。
