---
name: jupyter-live-kernel
description: Execute code in a live Jupyter kernel for data analysis and visualization
version: 1.0.0
tags: [jupyter, notebook, data-science, python, kernel, analysis]
category: data-science
platform: all
triggers: [jupyter, ノートブック, notebook, データ分析, data analysis, pandas, matplotlib, 可視化, visualization, kernel]
---

## 使用場面
データ分析の実行、matplotlib/seaborn による可視化、pandas でのデータ操作、機械学習モデルの実験。

## Jupyter カーネルへの接続・実行
```python
import jupyter_client

# 新しいカーネルを起動
km = jupyter_client.KernelManager(kernel_name='python3')
km.start_kernel()
kc = km.client()
kc.start_channels()

def execute_code(kc, code: str) -> dict:
    """コードを実行して結果を返す"""
    msg_id = kc.execute(code)
    outputs = []
    
    while True:
        try:
            msg = kc.get_iopub_msg(timeout=30)
            msg_type = msg['msg_type']
            content = msg['content']
            
            if msg_type == 'execute_result':
                outputs.append({"type": "result", "data": content['data']})
            elif msg_type == 'stream':
                outputs.append({"type": "stream", "text": content['text']})
            elif msg_type == 'display_data':
                outputs.append({"type": "display", "data": content['data']})
            elif msg_type == 'error':
                outputs.append({"type": "error", "traceback": content['traceback']})
            elif msg_type == 'status' and content['execution_state'] == 'idle':
                break
        except Exception:
            break
    
    return outputs

# 実行
results = execute_code(kc, """
import pandas as pd
import matplotlib.pyplot as plt
df = pd.DataFrame({'x': range(10), 'y': [i**2 for i in range(10)]})
print(df.describe())
""")
```

## よく使う分析パターン

### データ読み込みと探索 (EDA)
```python
import pandas as pd
import numpy as np

df = pd.read_csv("data.csv")
print(df.shape)          # 行数・列数
print(df.dtypes)         # データ型
print(df.isnull().sum()) # 欠損値の数
print(df.describe())     # 基本統計量
print(df.head(10))       # 最初の10行
```

### 可視化
```python
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# ヒストグラム
axes[0, 0].hist(df['value'], bins=30, color='steelblue')
axes[0, 0].set_title('Distribution')

# 相関ヒートマップ
sns.heatmap(df.corr(), annot=True, ax=axes[0, 1], cmap='coolwarm')

# 折れ線グラフ
axes[1, 0].plot(df['date'], df['sales'])
axes[1, 0].set_title('Sales Over Time')

plt.tight_layout()
plt.savefig('analysis.png', dpi=150)
plt.show()
```

### 機械学習
```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

X = df.drop('target', axis=1)
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
```

## 注意事項
- カーネルは終了後に必ず `km.shutdown_kernel()` で停止する
- 大きなデータは `dask` や `polars` でメモリ効率よく処理する
- グラフは `plt.savefig()` で保存してからレスポンスに含める

## 検証
コードが実行されてデータフレームや可視化結果が得られれば完了。
