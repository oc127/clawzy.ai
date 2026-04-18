---
name: writing-plans
description: Write clear, actionable implementation plans that align teams and reduce ambiguity
version: 1.0.0
tags: [plan, documentation, spec, design-doc, implementation]
category: software-dev
platform: all
triggers: [write plan, 計画書, 仕様書, spec, design doc, implementation plan, 実装計画, proposal, 提案書]
---

## 使用場面
チームでの設計合意形成、大規模機能のスコープ定義、技術的意思決定の記録。

## 実装計画書テンプレート

```markdown
# [機能名] 実装計画

## 背景・目的
なぜこれを作るのか。解決する問題。

## スコープ
### In Scope
- 実装する機能 A
- 実装する機能 B

### Out of Scope
- 将来対応する機能 X（理由）

## 技術設計

### データモデル変更
```python
class NewModel(Base):
    id: str = Column(UUID)
    # フィールド定義
```

### API 変更
| Method | Path | 説明 |
|--------|------|------|
| POST | /api/v1/xxx | 新規作成 |

### 処理フロー
1. ユーザーが XXX をリクエスト
2. バリデーション
3. DB 保存
4. レスポンス返却

## 実装ステップ
- [ ] Step 1: モデル定義（2h）
- [ ] Step 2: サービス層（4h）
- [ ] Step 3: API エンドポイント（2h）
- [ ] Step 4: テスト作成（3h）
- [ ] Step 5: フロントエンド（4h）

## リスクと対策
| リスク | 影響度 | 対策 |
|--------|--------|------|
| DB マイグレーション失敗 | 高 | ロールバックスクリプト準備 |

## 受入基準
- [ ] 全ての API テストが通る
- [ ] エラーハンドリングが実装されている
- [ ] ドキュメントが更新されている
```

## 良い計画書の特徴
1. **Why が明確**：なぜこのアプローチを選んだか
2. **具体的な変更ファイル**：ざっくりではなくファイル名まで
3. **時間見積もり**：ステップごとの工数
4. **代替案の検討**：なぜ採用しなかったか
5. **ロールバック計画**：問題時の対応

## 注意事項
- 計画書は生きたドキュメント。実装中に更新する
- 詳細過ぎる計画は書かない（コードが仕様書）
- レビュー者の視点で書く（知らない人が読む前提）

## 検証
チームメンバーが計画書を読んで実装を始められればOK。
