---
name: powerpoint
description: Create and modify PowerPoint presentations using python-pptx
version: 1.0.0
tags: [powerpoint, pptx, presentation, slides, office]
category: productivity
platform: all
triggers: [PowerPoint, プレゼン, スライド, PPTX, presentation, Keynote, 資料作成]
---

## 使用場面
プレゼンテーションの自動生成、スライドのバッチ更新、テンプレートからの資料作成。

## インストールと基本設定
```bash
pip install python-pptx
```

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
```

## プレゼンテーションの作成
```python
prs = Presentation()
prs.slide_width = Inches(16)
prs.slide_height = Inches(9)

# タイトルスライド
slide_layout = prs.slide_layouts[0]  # タイトルレイアウト
slide = prs.slides.add_slide(slide_layout)

title = slide.shapes.title
title.text = "月次レポート 2024年1月"
title.text_frame.paragraphs[0].font.size = Pt(40)
title.text_frame.paragraphs[0].font.bold = True
title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

subtitle = slide.placeholders[1]
subtitle.text = "開発チーム"
```

## コンテンツスライドの追加
```python
# 箇条書きスライド
layout = prs.slide_layouts[1]  # タイトルと内容
slide = prs.slides.add_slide(layout)
slide.shapes.title.text = "今月の成果"

tf = slide.placeholders[1].text_frame
tf.text = "スプリント完了率: 92%"

for item in ["機能 A を本番リリース", "バグ 15 件を修正", "パフォーマンス 30% 改善"]:
    p = tf.add_paragraph()
    p.text = item
    p.level = 1  # インデントレベル
    p.font.size = Pt(18)
```

## グラフの追加
```python
from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE

chart_data = ChartData()
chart_data.categories = ["1月", "2月", "3月"]
chart_data.add_series("売上", (100, 150, 130))

chart = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    Inches(1), Inches(2), Inches(8), Inches(5),
    chart_data
)
```

## 画像の追加
```python
slide.shapes.add_picture(
    "logo.png",
    left=Inches(0.5), top=Inches(0.5),
    width=Inches(2)
)
```

## 既存 PPTX の修正
```python
prs = Presentation("existing.pptx")
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if "旧テキスト" in run.text:
                        run.text = run.text.replace("旧テキスト", "新テキスト")

prs.save("updated.pptx")
```

## 注意事項
- フォントは日本語対応フォント（Noto Sans JP等）を指定する
- テンプレートを使うと一貫したデザインが保てる
- `.pptx` は XML ベース: `python-pptx` は非常に高機能

## 検証
生成した `.pptx` ファイルが PowerPoint/Keynote で開けば完了。
