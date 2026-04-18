---
name: hermes-agent-spawning
description: Spawn and orchestrate specialized sub-agents for complex multi-step tasks
version: 1.0.0
tags: [agent, spawn, orchestration, hermes, multi-agent, subagent]
category: agents
platform: all
triggers: [spawn agent, エージェント生成, orchestrate, オーケストレーション, multi-agent, マルチエージェント, 並列エージェント, parallel agents]
---

## 使用場面
複雑なタスクの並列化、専門エージェントへの委譲、大規模調査・実装の分割実行。

## エージェントスポーニングの原則

### タスク分解のフレームワーク
```
1. タスクを独立したサブタスクに分解する
2. 依存関係グラフを作成する
3. 独立タスクを並列エージェントに割り当てる
4. 依存タスクは直列で実行する
5. 結果を統合する
```

### スポーン指示のテンプレート
```
エージェントへの指示は必ず「自己完結」にする：

❌ 悪い例:
「前の会話で話した内容に基づいて実装して」

✅ 良い例:
「以下の仕様でスキルローダーを実装してください:
- ファイルパス: /project/backend/app/services/skill_loader.py
- 機能: YAML フロントマター付き SKILL.md を読み取り、compact list を返す
- テスト: pytest tests/test_skill_loader.py が通ること
- 既存コード: [関連コードを貼り付け]」
```

## オーケストレーターパターン

### 調査 → 実装 → テストの並列化
```python
# Round 1: 並列調査
agents = [
    spawn("Explore existing DB models", task="codebase-inspection"),
    spawn("Research FastAPI best practices", task="web-search"),
    spawn("Design API schema", task="planning"),
]
results = await gather(*agents)

# Round 2: 並列実装（調査結果を渡す）
impl_agents = [
    spawn("Implement model", context=results[0]),
    spawn("Implement service", context=results[0]),
    spawn("Write tests", context=results[0]),
]
```

### 専門エージェントタイプ
| タイプ | 得意分野 |
|--------|---------|
| Explorer | コードベース調査・ファイル検索 |
| Engineer | 実装・コーディング |
| Researcher | Web 検索・情報収集 |
| Reviewer | コードレビュー・QA |
| Planner | 設計・アーキテクチャ |

## 結果の統合チェックリスト
```
□ 各エージェントの変更が競合していないか
□ 共通の型・インターフェースが一致しているか
□ テストが全体的に通るか
□ 命名規則・コーディングスタイルが統一されているか
□ エラーハンドリングが漏れていないか
```

## エージェントへのコンテキスト渡し方
```
# ファイルパスを明示する
「`backend/app/services/skill_service.py` の 155-180 行目の
inject_skills_to_prompt() 関数を修正してください...」

# 期待する出力を明示する
「関数を実装して、pytest で以下のテストが通ることを確認してください:
assert list_all_skills() returns list of SkillMeta objects」
```

## 注意事項
- エージェント数は 3〜5 が最適（多すぎると統合コストが増大）
- 各エージェントには単一の明確な責務を与える
- 結果は必ず親エージェントが検証・統合する

## 検証
全サブエージェントが完了し、統合後のテストが通れば成功。
