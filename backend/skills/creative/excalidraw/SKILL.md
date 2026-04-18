---
name: excalidraw
description: Create and export Excalidraw diagrams programmatically for architecture and flows
version: 1.0.0
tags: [excalidraw, diagram, architecture, drawing, visualization]
category: creative
platform: all
triggers: [excalidraw, 図, diagram, アーキテクチャ図, フロー図, 設計図, drawing, 手書き風]
---

## 使用場面
システムアーキテクチャ図の生成、フローチャートの作成、インフラ構成図の自動生成。

## Excalidraw JSON 形式
```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "rect-1",
      "type": "rectangle",
      "x": 100, "y": 100,
      "width": 200, "height": 80,
      "strokeColor": "#1971c2",
      "backgroundColor": "#d0ebff",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "roughness": 1,
      "opacity": 100,
      "text": ""
    },
    {
      "id": "text-1",
      "type": "text",
      "x": 150, "y": 130,
      "text": "OpenClaw Backend",
      "fontSize": 16,
      "fontFamily": 1,
      "textAlign": "center",
      "strokeColor": "#1971c2"
    },
    {
      "id": "arrow-1",
      "type": "arrow",
      "x": 300, "y": 140,
      "points": [[0, 0], [100, 0]],
      "strokeColor": "#2f9e44",
      "strokeWidth": 2,
      "startArrowhead": null,
      "endArrowhead": "arrow"
    }
  ],
  "appState": {
    "viewBackgroundColor": "#ffffff"
  }
}
```

## Python でダイアグラムを生成
```python
import json
import uuid

def create_box(x, y, w, h, label, color="#1971c2", bg="#d0ebff"):
    eid = str(uuid.uuid4())[:8]
    return [
        {
            "id": f"rect-{eid}",
            "type": "rectangle",
            "x": x, "y": y, "width": w, "height": h,
            "strokeColor": color, "backgroundColor": bg,
            "fillStyle": "solid", "strokeWidth": 2,
            "roughness": 1, "opacity": 100,
        },
        {
            "id": f"text-{eid}",
            "type": "text",
            "x": x + w/2, "y": y + h/2 - 8,
            "text": label, "fontSize": 14,
            "fontFamily": 1, "textAlign": "center",
            "strokeColor": color,
        }
    ]

def create_arrow(x1, y1, x2, y2, label=""):
    return {
        "id": str(uuid.uuid4())[:8],
        "type": "arrow",
        "x": x1, "y": y1,
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "strokeColor": "#343a40",
        "strokeWidth": 2,
        "endArrowhead": "arrow",
    }

# アーキテクチャ図の生成
elements = []
elements += create_box(100, 100, 200, 60, "Frontend")
elements += create_box(400, 100, 200, 60, "Backend API")
elements += create_box(700, 100, 200, 60, "LLM Service")
elements.append(create_arrow(300, 130, 400, 130))
elements.append(create_arrow(600, 130, 700, 130))

diagram = {
    "type": "excalidraw",
    "version": 2,
    "elements": elements,
    "appState": {"viewBackgroundColor": "#ffffff"}
}

with open("architecture.excalidraw", "w") as f:
    json.dump(diagram, f, indent=2)

print("ファイルを https://excalidraw.com で開いてください")
```

## 注意事項
- `.excalidraw` ファイルは https://excalidraw.com にドラッグ&ドロップで開ける
- `roughness: 0` でクリーン、`1` で手書き風、`2` でラフな外観
- 色は Excalidraw のパレット（`#1971c2`, `#2f9e44`, `#e03131` 等）を使うと統一感が出る

## 検証
`.excalidraw` ファイルが Excalidraw で正しく表示されれば完了。
