---
name: github-issues
description: Create, triage, and manage GitHub Issues for bug tracking and feature requests
version: 1.0.0
tags: [github, issues, bug-tracking, project-management]
category: github
platform: all
triggers: [github issue, イシュー, bug report, feature request, バグ報告, create issue, close issue, milestone]
---

## 使用場面
バグ報告、機能リクエストの管理、スプリントの計画、技術的負債の追跡。

## Issue 管理

### Issue の作成
```bash
# バグ報告
gh issue create \
  --title "fix: skill loader returns empty list when skills/ dir missing" \
  --body "$(cat <<'EOF'
## 再現手順
1. `backend/skills/` ディレクトリを削除
2. `GET /skills/builtin` を叩く
3. 500 エラーではなく空配列を期待するが、例外が発生

## 期待する動作
空配列 `[]` を返す

## 実際の動作
`FileNotFoundError: No such file or directory: 'skills'`

## 環境
- Python 3.11
- OpenClaw v1.2.0
EOF
)" \
  --label "bug" \
  --assignee "@me"

# 機能リクエスト
gh issue create \
  --title "feat: skill search by category filter" \
  --label "enhancement" \
  --milestone "v1.1"
```

### Issue の一覧・フィルタリング
```bash
# open な自分のアサイン
gh issue list --assignee "@me" --state open

# ラベルでフィルタ
gh issue list --label "bug" --label "high-priority"

# マイルストーン別
gh issue list --milestone "v1.0"
```

### Issue のクローズ
```bash
# コメントしてクローズ
gh issue close 42 --comment "PR #55 でフィックスしました"

# 重複としてクローズ
gh issue close 42 --comment "Duplicate of #30"
```

## Issue テンプレート設計
```markdown
## バグ報告テンプレート
**再現手順:** 1. ... 2. ...
**期待:** ...
**実際:** ...
**環境:** OS, バージョン

## 機能リクエストテンプレート
**現状の問題:** ...
**提案する解決策:** ...
**代替案:** ...
```

## ラベル設計
| ラベル | 用途 |
|--------|------|
| `bug` | 不具合 |
| `enhancement` | 新機能 |
| `high-priority` | 優先度高 |
| `good-first-issue` | 初心者向け |
| `blocked` | 他に依存 |

## 注意事項
- タイトルは動詞で始める（fix:, feat:, docs:）
- 再現手順は必ず含める
- スクリーンショットは価値が高い

## 検証
`gh issue view 42` で正しい情報が表示されれば完了。
