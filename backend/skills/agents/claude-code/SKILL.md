---
name: claude-code
description: Use Claude Code CLI for autonomous coding tasks, file editing, and codebase navigation
version: 1.0.0
tags: [claude-code, cli, coding, agent, autonomous]
category: agents
platform: all
triggers: [claude code, Claude Code, CLI, 自律コーディング, コード自動生成, autonomous coding, claude cli]
---

## 使用場面
ターミナルから直接コードを生成・編集、複雑なリファクタリングの自動化、コードベースの調査と修正。

## 基本的な使い方

### インタラクティブセッション
```bash
# カレントディレクトリでセッション開始
claude

# 特定のプロジェクトディレクトリで
claude --project /path/to/project
```

### ワンショットコマンド
```bash
# 単一タスクを実行して終了
claude -p "バグを修正して: AttributeError at line 42 in skill_loader.py"

# ファイルを指定して質問
claude -p "この関数を最適化して" < backend/app/services/skill_service.py

# パイプラインで使用
git diff HEAD | claude -p "このコード変更のコードレビューをして"
```

## 便利なスラッシュコマンド

| コマンド | 説明 |
|---------|------|
| `/help` | ヘルプ表示 |
| `/clear` | 会話履歴をクリア |
| `/compact` | 会話を圧縮して継続 |
| `/model` | モデルを切り替え |
| `/review` | PRのコードレビュー |
| `/init` | CLAUDE.md を初期化 |

## CLAUDE.md によるカスタマイズ
```markdown
# CLAUDE.md
プロジェクトの規約や指示をここに書く。

## コーディング規約
- Python: PEP 8 準拠
- 関数名: snake_case
- テスト: pytest 使用

## よく使うコマンド
- テスト実行: pytest -v
- Lint: ruff check .
- 型チェック: mypy backend/
```

## MCP (Model Context Protocol) の活用
```bash
# ~/.claude/claude.json に MCP サーバーを設定
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"]
    }
  }
}
```

## 権限モード
```bash
# 全ての操作を自動承認（注意して使用）
claude --dangerously-skip-permissions

# 特定のパターンを許可
# settings.json の permissions.allow に追加
```

## よくあるタスク例
```bash
# テストを書いてもらう
claude -p "skill_loader.py の list_all_skills() のユニットテストを書いて"

# コードレビュー
git diff origin/main | claude -p "このPRをレビューして問題点を指摘して"

# バグ修正
claude -p "pytest が failing している: $(pytest 2>&1 | tail -30)"
```

## 注意事項
- `--dangerously-skip-permissions` は信頼できる環境でのみ使用
- 破壊的操作（`rm -rf`、DB drop）は必ず確認を求める
- センシティブなファイル（`.env`）が誤って読まれないよう `.claudeignore` を設定

## 検証
`claude --version` が表示されれば動作確認完了。
