---
name: obsidian
description: Create, read, and link notes in Obsidian vault using file system and Obsidian URI
version: 1.0.0
tags: [obsidian, notes, markdown, vault, knowledge-base, zettelkasten]
category: note-taking
platform: all
triggers: [Obsidian, ノート管理, vault, 知識ベース, zettelkasten, ノート作成, note taking, マークダウン]
---

## 使用場面
ナレッジベースへのメモ追加、既存ノートの参照・更新、Daily Note の作成、タグ管理。

## ファイルシステム直接操作
```python
from pathlib import Path
from datetime import datetime

VAULT_PATH = Path("/Users/username/Documents/MyVault")

def create_note(title: str, content: str, folder: str = "", tags: list[str] = None) -> Path:
    """新しいノートを作成"""
    frontmatter = f"""---
title: {title}
date: {datetime.now().strftime("%Y-%m-%d")}
tags: [{', '.join(tags or [])}]
---

"""
    note_dir = VAULT_PATH / folder if folder else VAULT_PATH
    note_dir.mkdir(parents=True, exist_ok=True)
    
    note_path = note_dir / f"{title}.md"
    note_path.write_text(frontmatter + content, encoding="utf-8")
    return note_path

def search_notes(query: str) -> list[dict]:
    """ノートをキーワード検索"""
    results = []
    for md_file in VAULT_PATH.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        if query.lower() in content.lower():
            results.append({
                "path": str(md_file.relative_to(VAULT_PATH)),
                "title": md_file.stem,
                "preview": content[:200]
            })
    return results
```

## Daily Note の作成
```python
def create_daily_note(tasks: list[str] = None, notes: str = "") -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    task_list = "\n".join(f"- [ ] {t}" for t in (tasks or []))
    
    content = f"""## タスク
{task_list}

## メモ
{notes}

## 振り返り
- 

## リンク
"""
    return create_note(today, content, folder="Daily Notes", tags=["daily"])
```

## Obsidian URI でアプリを制御
```python
import subprocess
import urllib.parse

def open_note(vault_name: str, note_path: str):
    """Obsidian で特定のノートを開く"""
    encoded_path = urllib.parse.quote(note_path)
    uri = f"obsidian://open?vault={vault_name}&file={encoded_path}"
    subprocess.run(["open", uri])  # macOS

def create_note_via_uri(vault_name: str, title: str, content: str):
    """Obsidian URI 経由でノートを新規作成"""
    encoded_content = urllib.parse.quote(content)
    uri = f"obsidian://new?vault={vault_name}&name={title}&content={encoded_content}"
    subprocess.run(["open", uri])
```

## Dataview クエリ（Obsidian プラグイン）
````markdown
```dataview
TABLE date, tags
FROM "Daily Notes"
WHERE date >= date(today) - dur(7 days)
SORT date DESC
```
````

## ウィキリンクの管理
```python
import re

def extract_wikilinks(content: str) -> list[str]:
    """[[リンク]] 形式のリンクを抽出"""
    return re.findall(r'\[\[([^\]]+)\]\]', content)

def add_backlink(from_note: str, to_note: str):
    """バックリンクを追加"""
    note_path = VAULT_PATH / f"{from_note}.md"
    content = note_path.read_text(encoding="utf-8")
    if f"[[{to_note}]]" not in content:
        note_path.write_text(content + f"\n- [[{to_note}]]")
```

## 注意事項
- ボールト内のファイルを直接編集すると同期に反映される
- `.obsidian/` フォルダはプラグイン設定（編集しない）
- YAML frontmatter は `---` で囲む

## 検証
Obsidian を開いてノートが作成・更新されていれば完了。
