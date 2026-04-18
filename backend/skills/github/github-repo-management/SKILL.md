---
name: github-repo-management
description: Manage GitHub repository settings, branches, releases, and team permissions
version: 1.0.0
tags: [github, repository, branch-protection, releases, settings]
category: github
platform: all
triggers: [repo settings, リポジトリ設定, branch protection, ブランチ保護, release, リリース, tag, collaborator, 権限]
---

## 使用場面
ブランチ保護ルールの設定、リリース作成、コラボレーター管理、リポジトリ設定の変更。

## ブランチ保護ルール
```bash
# main ブランチを保護（直接 push 禁止、PR 必須）
gh api repos/OWNER/REPO/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci/tests"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

## リリース管理
```bash
# タグを作成してリリース
git tag -a v1.2.0 -m "Release v1.2.0: built-in skill library"
git push origin v1.2.0

# GitHub Release を作成
gh release create v1.2.0 \
  --title "v1.2.0 — Built-in Skill Library" \
  --notes "$(cat <<'EOF'
## 新機能
- 35+ 内蔵スキルライブラリ（ディスクベース）
- スキルの段階的開示ローディング
- GET /skills/builtin API

## バグ修正
- スキル注入時の N+1 クエリを修正

## 破壊的変更
なし
EOF
)" \
  --latest

# プレリリース
gh release create v1.3.0-beta.1 --prerelease
```

## コラボレーター管理
```bash
# コラボレーターを招待
gh api repos/OWNER/REPO/collaborators/USERNAME \
  --method PUT \
  --field permission=push  # pull, push, admin

# 一覧確認
gh api repos/OWNER/REPO/collaborators
```

## リポジトリ設定
```bash
# デフォルトブランチの変更
gh api repos/OWNER/REPO \
  --method PATCH \
  --field default_branch=main

# Wiki・Issues を無効化
gh api repos/OWNER/REPO \
  --method PATCH \
  --field has_wiki=false \
  --field has_issues=true
```

## Webhook 設定
```bash
gh api repos/OWNER/REPO/hooks \
  --method POST \
  --field name=web \
  --field 'config[url]=https://example.com/webhook' \
  --field 'config[content_type]=json' \
  --field 'events[]=push' \
  --field 'events[]=pull_request' \
  --field active=true
```

## 注意事項
- リリースノートには破壊的変更を必ず明記する
- ブランチ保護は force push も禁止する
- `GITHUB_TOKEN` のスコープに注意

## 検証
`gh repo view` でリポジトリの設定が反映されていれば完了。
