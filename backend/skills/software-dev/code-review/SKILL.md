---
name: code-review
description: Systematic code review covering correctness, security, performance, and maintainability
version: 1.0.0
tags: [review, quality, security, best-practices]
category: software-dev
platform: all
triggers: [review, レビュー, コードレビュー, check code, code quality, pull request review, PR review]
---

## 使用場面
コードの品質確認、PR レビュー、セキュリティ検査、技術的負債の特定に使用する。

## レビュー観点（優先順）

### 1. 正確性
- ロジックが仕様通りか
- エッジケース（空値、ゼロ除算、オーバーフロー）の処理
- エラーハンドリングの網羅性
- 非同期処理の競合状態

### 2. セキュリティ
- SQLインジェクション・XSS・CSRF の脆弱性
- シークレット・認証情報のハードコード禁止
- 入力バリデーションの実施
- 権限チェックの漏れ

### 3. パフォーマンス
- N+1 クエリ問題
- 不必要なループや再計算
- キャッシュの活用機会
- 大量データ処理時のメモリ効率

### 4. 可読性・保守性
- 関数・変数命名の明確さ
- 単一責任の原則
- 重複コードの排除（DRY）
- テスト容易性

## レビューフォーマット
```
## コードレビュー結果

### 重大な問題 🔴
- [行番号] 説明と修正案

### 要改善 🟡
- [行番号] 説明と改善提案

### 軽微な提案 🟢
- [行番号] スタイルや最適化の提案

### 良い点 ✅
- 称賛すべき実装
```

## 注意事項
- 人格攻撃ではなくコードを批評する
- 修正案を必ず提示する
- LGTM だけでなく理由も記載する

## 検証
レビューコメントが具体的な行番号と修正提案を含んでいれば完了。
