---
name: codebase-inspection
description: Systematically explore and understand an unfamiliar codebase
version: 1.0.0
tags: [explore, codebase, understand, navigation, grep, architecture]
category: github
platform: all
triggers: [explore codebase, コードベース調査, understand code, コードを理解, find file, ファイル探す, how does X work, どう動く, architecture, 構造]
---

## 使用場面
新しいリポジトリへの入場、特定機能の実装場所の特定、依存関係の把握、バグ調査の起点。

## 調査プロセス

### Step 1: 全体把握（3 分）
```bash
# ディレクトリ構造の把握
find . -type f -name "*.py" | head -50
ls -la

# README と主要設定ファイルを読む
cat README.md
cat pyproject.toml  # または package.json, Cargo.toml

# エントリーポイントを探す
cat main.py  # または index.ts, app.py
```

### Step 2: アーキテクチャの把握
```bash
# 主要ディレクトリの役割を確認
ls backend/app/
# → models/, services/, api/, core/ などのパターンを把握

# 依存関係グラフ（Python）
pipdeptree 2>/dev/null | head -30
```

### Step 3: 特定機能の追跡
```bash
# キーワードで検索（-n で行番号, -r で再帰）
grep -rn "inject_skills" backend/ --include="*.py"

# 関数定義を探す
grep -rn "^def\|^async def" backend/app/services/ --include="*.py"

# クラス定義
grep -rn "^class " backend/app/models/ --include="*.py"

# import 関係
grep -rn "from app.services" backend/app/api/ --include="*.py"
```

### Step 4: データモデルの把握
```bash
# DB モデルの全フィールド確認
cat backend/app/models/skill.py

# マイグレーション履歴
ls backend/alembic/versions/ | sort
```

### Step 5: API エンドポイントの把握
```bash
# ルーター定義を見つける
grep -rn "router.get\|router.post\|router.put\|router.delete" \
  backend/app/api/ --include="*.py"

# FastAPI の場合
python -c "from app.main import app; print([r.path for r in app.routes])"
```

## よく使うパターン
```bash
# TODO/FIXME を探す
grep -rn "TODO\|FIXME\|HACK\|XXX" src/ --include="*.py"

# テストファイルを見る
find . -name "test_*.py" -o -name "*_test.py" | head -20

# 最近変更されたファイル
git log --name-only --pretty=format: -20 | sort -u | head -20

# 誰が書いたか
git log --follow -p path/to/file.py
```

## 注意事項
- まず読んで理解してから変更する（30 分ルール）
- テストファイルはドキュメントとして読む
- git blame で「なぜ」を調べる

## 検証
主要コンポーネントとそのファイルパスをリストできれば理解完了。
