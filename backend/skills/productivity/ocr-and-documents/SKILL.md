---
name: ocr-and-documents
description: Extract text from images and PDFs using OCR tools and document processing
version: 1.0.0
tags: [ocr, pdf, document, text-extraction, image-to-text]
category: productivity
platform: all
triggers: [OCR, 文字認識, PDF, 画像からテキスト, extract text, ドキュメント解析, スキャン, scan]
---

## 使用場面
画像内のテキスト抽出、PDF のテキスト変換、スキャン文書の処理、請求書・領収書の読み取り。

## Python OCR ライブラリ

### Tesseract（ローカル OCR）
```bash
# インストール
brew install tesseract tesseract-lang
pip install pytesseract Pillow
```

```python
import pytesseract
from PIL import Image

# 画像からテキスト抽出
img = Image.open("invoice.jpg")
text = pytesseract.image_to_string(img, lang="jpn+eng")
print(text)

# 信頼度スコア付きで取得
data = pytesseract.image_to_data(img, lang="jpn", output_type=pytesseract.Output.DICT)
```

### PDF からテキスト抽出
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        print(f"--- Page {i+1} ---")
        print(text)
        
        # テーブル抽出
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                print(row)
```

### 画像の前処理（認識率向上）
```python
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

def preprocess_image(image_path: str) -> Image:
    img = Image.open(image_path).convert('L')  # グレースケール
    img = img.filter(ImageFilter.SHARPEN)       # シャープ化
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)                  # コントラスト強調
    return img

text = pytesseract.image_to_string(preprocess_image("scan.jpg"), lang="jpn")
```

### Claude Vision API でのOCR（高精度）
```python
import anthropic
import base64

client = anthropic.Anthropic()

with open("invoice.jpg", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
            {"type": "text", "text": "この請求書から金額、日付、品目を JSON 形式で抽出してください"}
        ]
    }]
)
print(response.content[0].text)
```

## 注意事項
- 日本語は `lang="jpn"` を指定する（Tesseract）
- 解像度は 300 DPI 以上が推奨
- 手書き文字は AI モデルの方が精度が高い

## 検証
テキストが正確に抽出され、JSON 等の構造化データに変換できれば完了。
