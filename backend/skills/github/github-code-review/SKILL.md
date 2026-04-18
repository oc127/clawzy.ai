---
name: github-code-review
description: Perform structured code reviews on GitHub PRs using gh CLI
version: 1.0.0
tags: [github, review, pr, code-review, gh-cli]
category: github
platform: all
triggers: [review PR, PRレビュー, github review, コードレビュー, gh pr review, approve, request changes]
---

## 使用場面
GitHub PR のコードレビュー実施、承認・却下・コメントの投稿、レビュー依頼への対応。

## レビュープロセス

### Step 1: PR の概要把握
```bash
# PR の概要と変更ファイルを確認
gh pr view 123
gh pr diff 123

# 変更の統計
gh pr diff 123 --stat
```

### Step 2: ローカルでチェックアウト（任意）
```bash
# 実際に動かして確認
gh pr checkout 123
python -m pytest tests/
```

### Step 3: インラインコメント
```bash
# ファイル + 行番号でコメント
gh api repos/OWNER/REPO/pulls/123/comments \
  --method POST \
  --field body="この実装だと N+1 クエリが発生します。`select_related()` を検討してください。" \
  --field commit_id="$(gh pr view 123 --json headRefOid -q '.headRefOid')" \
  --field path="backend/app/services/skill_service.py" \
  --field line=145
```

### Step 4: レビュー結論を投稿
```bash
# 承認
gh pr review 123 --approve --body "LGTM! テストカバレッジも十分です。"

# 変更依頼
gh pr review 123 --request-changes --body "セキュリティ上の懸念があります。詳細はインラインコメントを参照。"

# コメントのみ（承認も却下もしない）
gh pr review 123 --comment --body "いくつか質問があります。"
```

## レビューチェックリスト
```
□ テストが追加または更新されているか
□ 破壊的な API 変更がないか（ある場合はドキュメント更新）
□ エラーハンドリングが適切か
□ ログ出力にシークレットが含まれていないか
□ パフォーマンス上の懸念がないか
□ 命名が一貫しているか
```

## レビューコメントの書き方
```
# 良い例
「L45: `await db.commit()` が例外時にロールバックされません。
try/finally で db.rollback() を呼ぶか、トランザクションコンテキストを使ってください。」

# 悪い例
「このコードは間違っています」（理由・修正案なし）
```

## 注意事項
- `gh` は `gh auth login` で認証済みであること
- レビューは 24 時間以内に返す（SLA 設定推奨）
- blocking comment と non-blocking comment を区別する

## 検証
`gh pr view 123 --json reviews` でレビューが記録されていれば完了。
