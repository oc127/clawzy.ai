---
name: plan
description: Think through implementation strategy before writing any code
version: 1.0.0
tags: [plan, design, architecture, strategy, approach]
category: software-dev
platform: all
triggers: [plan, 計画, 設計, design, architecture, アーキテクチャ, approach, どう実装, how to implement, before coding, 実装前]
---

## 使用場面
新機能の実装前、複雑な変更の前、技術的なアーキテクチャ決定が必要な場面。

## 計画フレームワーク

### Step 1: 問題の明確化
- 何を解決するのか？（ユーザーストーリー）
- 成功条件は何か？（受入基準）
- スコープ外は何か？

### Step 2: 現状の把握
```bash
# 関連コードを調査する
grep -r "関連キーワード" src/
cat src/relevant_file.py
```
- 既存のパターンや規約を確認する
- 依存関係を把握する
- 技術的負債を把握する

### Step 3: アプローチの選択
各案を検討する：
```
案 A: XXX
  利点: シンプル、既存パターンと一貫
  欠点: スケールしない
  
案 B: YYY  
  利点: 堅牢、テスタブル
  欠点: 実装コスト高い
  
採用: 案 A（理由: 現在の規模では十分、将来は B に移行可能）
```

### Step 4: 実装ステップを列挙
1. データモデルの変更（マイグレーション）
2. サービス層の実装
3. API エンドポイントの追加
4. テストの作成
5. フロントエンドの更新

### Step 5: リスク評価
- 破壊的変更（DB マイグレーション・API 変更）
- パフォーマンス影響
- セキュリティ考慮
- ロールバック計画

## 計画の出力フォーマット
```markdown
## 実装計画: [機能名]

### 概要
1 〜 2 文で何をするか。

### 変更ファイル
- `src/models/xxx.py` — スキーマ追加
- `src/services/xxx.py` — ビジネスロジック
- `tests/test_xxx.py` — テスト

### 実装順序
1. ...
2. ...

### 注意点
- ...
```

## 注意事項
- 計画は完璧でなくてよい。実装中に学んだことで更新する
- 計画のためだけに多くの時間を使わない（15 分を目安）
- 実装を始めたら計画を参照し続ける

## 検証
計画が変更ファイルと実装順序を含んでいれば着手可能。
