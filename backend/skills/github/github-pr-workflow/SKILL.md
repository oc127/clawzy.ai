---
name: github-pr-workflow
description: End-to-end Pull Request workflow from branch creation to merge
version: 1.0.0
tags: [github, pr, pull-request, merge, git, workflow]
category: github
platform: all
triggers: [PR, pull request, プルリクエスト, プルリク, merge, マージ, create branch, ブランチ, git flow]
---

## 使用場面
新機能・バグ修正の PR 作成、コードレビューのリクエスト、マージフローの実行。

## PR ワークフロー

### Step 1: ブランチ作成
```bash
# main から最新を取得
git checkout main && git pull origin main

# 機能ブランチを作成
git checkout -b feat/add-skill-loader
# feat/, fix/, chore/, docs/ のプレフィックスを使う
```

### Step 2: 変更とコミット
```bash
# 関連ファイルのみをステージング
git add backend/app/services/skill_loader.py

# 規約に沿ったコミットメッセージ
git commit -m "feat(skills): add disk-based skill loader service

- list_all_skills() for compact index
- get_skill(name) for on-demand full content
- match_skills() for trigger-based matching"
```

### Step 3: PR 作成
```bash
gh pr create \
  --title "feat(skills): add built-in skill library" \
  --body "$(cat <<'EOF'
## Summary
- 35+ built-in skills stored as SKILL.md files
- Progressive disclosure loading (list → full content on demand)
- Merged with existing DB-backed custom skills

## Test Plan
- [ ] `list_all_skills()` returns compact index
- [ ] `match_skills("debug")` matches systematic-debugging
- [ ] GET /skills/builtin returns all built-ins
EOF
)" \
  --base main \
  --draft
```

### Step 4: レビュー対応
```bash
# レビューコメントへの修正
git add -p  # 変更を確認しながらステージング
git commit -m "fix: address review comments on skill loader"
git push origin feat/add-skill-loader
```

### Step 5: マージ
```bash
# CI が通ってから
gh pr merge --squash --delete-branch
```

## PR タイトル規約
```
feat(scope):  新機能
fix(scope):   バグ修正
chore(scope): 設定・依存関係
docs(scope):  ドキュメント
refactor:     リファクタリング
test:         テスト追加
```

## 注意事項
- PR は 400 行以下を目標（大きいと review されない）
- Draft PR で早めにフィードバックを得る
- force push は shared branch では禁止

## 検証
`gh pr view` で PR が open 状態、CI が passing であれば OK。
