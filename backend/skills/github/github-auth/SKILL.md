---
name: github-auth
description: Set up and manage GitHub authentication for CLI and API access
version: 1.0.0
tags: [github, auth, token, ssh, cli, permissions]
category: github
platform: all
triggers: [github auth, 認証, token, SSH key, login, gh auth, git push permission, 権限エラー]
---

## 使用場面
GitHub CLI の認証設定、Personal Access Token の作成、SSH キーの設定、CI/CD 環境の認証設定。

## GitHub CLI 認証
```bash
# ブラウザ経由で認証（推奨）
gh auth login
# → GitHub.com → HTTPS → Y (ブラウザで認証)

# Token で認証（CI 環境）
echo "ghp_xxxxxxxxxxxx" | gh auth login --with-token

# 現在の認証状態確認
gh auth status
```

## Personal Access Token (PAT) の作成
```bash
# CLI から作成（細かいスコープ指定）
gh auth token  # 現在のトークンを確認

# Web から作成
# Settings → Developer settings → Personal access tokens → Fine-grained tokens
```

### 必要なスコープ
| 用途 | 必要なスコープ |
|------|--------------|
| コードの読み取り | `repo:read` |
| PR/Issue 操作 | `repo` |
| Actions | `workflow` |
| パッケージ | `write:packages` |
| Admin | `admin:repo` |

## SSH キー設定
```bash
# SSH キーを生成
ssh-keygen -t ed25519 -C "your@email.com"

# 公開鍵を GitHub に追加
gh ssh-key add ~/.ssh/id_ed25519.pub --title "My MacBook"

# 接続テスト
ssh -T git@github.com
# → Hi username! You've successfully authenticated
```

## Git リモートの設定
```bash
# HTTPS → SSH に切り替え
git remote set-url origin git@github.com:OWNER/REPO.git

# HTTPS（Token）を使う場合
git remote set-url origin https://TOKEN@github.com/OWNER/REPO.git

# 確認
git remote -v
```

## CI/CD 環境（GitHub Actions）
```yaml
# .github/workflows/ci.yml
- name: Checkout
  uses: actions/checkout@v4

- name: GitHub CLI 認証
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: gh pr comment ${{ github.event.number }} --body "CI passed"
```

## 注意事項
- PAT はリポジトリごとの Fine-grained tokens を使う（セキュリティ）
- トークンは環境変数か Secret Manager に保存。コードに書かない
- `GITHUB_TOKEN` は Actions 内で自動提供される

## 検証
`gh api user` でユーザー情報が返れば認証完了。
