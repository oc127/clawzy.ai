---
name: ascii-art
description: Generate ASCII art from text, images, or descriptions
version: 1.0.0
tags: [ascii, art, creative, text-art, terminal]
category: creative
platform: all
triggers: [ASCII art, アスキーアート, テキストアート, ascii, 文字アート, terminal art, figlet]
---

## 使用場面
ターミナル出力の装飾、CLI ツールのバナー作成、テキストベースのビジュアル表現。

## figlet / pyfiglet でテキストアート
```python
import pyfiglet  # pip install pyfiglet

# シンプルなバナー
result = pyfiglet.figlet_format("OpenClaw", font="slant")
print(result)
#   ____                   ______  __
#  / __ \____  ___  ____  / ____/ / /___ __      __
# / / / / __ \/ _ \/ __ \/ /     / / __ `/ | /| / /
#/ /_/ / /_/ /  __/ / / / /___  / / /_/ /| |/ |/ /
#\____/ .___/\___/_/ /_/\____/ /_/\__,_/ |__/|__/
#    /_/

# フォント一覧
fonts = pyfiglet.FigletFont.getFonts()
print(f"利用可能なフォント数: {len(fonts)}")
```

## プログレスバーと装飾
```python
# シンプルなプログレスバー
def progress_bar(current: int, total: int, width: int = 40) -> str:
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    pct = current / total * 100
    return f"[{bar}] {pct:.1f}%"

# ボックス描画
def box(text: str) -> str:
    lines = text.split("\n")
    w = max(len(l) for l in lines) + 2
    top    = "╔" + "═" * w + "╗"
    bottom = "╚" + "═" * w + "╝"
    body   = "\n".join(f"║ {l.ljust(w-2)} ║" for l in lines)
    return f"{top}\n{body}\n{bottom}"

print(box("Hello\nOpenClaw!"))
# ╔══════════╗
# ║ Hello    ║
# ║ OpenClaw!║
# ╚══════════╝
```

## 画像 → ASCII 変換
```python
from PIL import Image

def image_to_ascii(path: str, width: int = 80) -> str:
    chars = "@%#*+=-:. "
    img = Image.open(path).convert("L")  # グレースケール
    aspect = img.height / img.width
    height = int(width * aspect * 0.5)
    img = img.resize((width, height))
    
    result = []
    for y in range(height):
        row = ""
        for x in range(width):
            pixel = img.getpixel((x, y))
            row += chars[int(pixel / 256 * len(chars))]
        result.append(row)
    return "\n".join(result)
```

## よく使う ASCII 記号
```
罫線: ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼
二重: ═ ║ ╔ ╗ ╚ ╝ ╠ ╣ ╦ ╩ ╬
ブロック: █ ▉ ▊ ▋ ▌ ▍ ▎ ▏ ░ ▒ ▓
矢印: → ← ↑ ↓ ↔ ↕ ⇒ ⇐ ⇑ ⇓
図形: ● ○ ◆ ◇ ■ □ ▲ △ ▼ ▽
```

## カラー付き出力（ANSI）
```python
RED   = "\033[91m"
GREEN = "\033[92m"
BLUE  = "\033[94m"
RESET = "\033[0m"
BOLD  = "\033[1m"

print(f"{GREEN}{BOLD}✓ Success{RESET}")
print(f"{RED}✗ Error{RESET}")
```

## 注意事項
- 日本語フォントは figlet では対応不可（pyfiglet も同様）
- 全角文字はレイアウトがずれる場合がある
- ターミナルのフォント設定によって表示が異なる

## 検証
ターミナルでアート・バナーが正しく表示されれば完了。
