---
name: systematic-debugging
description: Step-by-step debugging methodology to isolate and fix bugs efficiently
version: 1.0.0
tags: [debug, bug, error, troubleshoot, fix]
category: software-dev
platform: all
triggers: [debug, デバッグ, バグ, bug, error, エラー, not working, 動かない, 原因, fix, 直す, crash, exception]
---

## 使用場面
バグの原因調査、予期しない動作の解析、エラーメッセージの解読、パフォーマンス問題の特定。

## デバッグプロセス

### Phase 1: 問題の再現
1. 問題を最小限の手順で再現する
2. 再現条件を文書化する（OS・バージョン・入力値）
3. 毎回再現するか、まれに発生するかを確認

### Phase 2: 情報収集
```bash
# ログ確認
tail -f logs/app.log | grep ERROR

# スタックトレースの最後から読む（根本原因は末尾）
Traceback (most recent call last):
  File "app.py", line 42, in handler   # ← ここから
  ...
AttributeError: 'NoneType' has no attr  # ← 実際の原因
```

### Phase 3: 仮説を立てる
問いかけ：
- 最後に何を変更したか？
- 正常時と異常時の差は何か？
- エラーが発生する入力の共通点は？

### Phase 4: 仮説の検証（二分探索）
```python
# print デバッグ（素早く）
print(f"DEBUG: user={user!r}, credits={credits}")

# ブレークポイント（詳細調査）
import pdb; pdb.set_trace()

# アサーションで状態確認
assert isinstance(amount, int), f"Expected int, got {type(amount)}"
```

### Phase 5: 修正と確認
1. 根本原因を修正する（症状ではなく）
2. 単体テストを追加してリグレッションを防ぐ
3. 類似コードに同じバグがないか確認する

## よくある原因パターン
| 症状 | 原因候補 |
|------|---------|
| NoneType エラー | None チェック漏れ、DB レコード未存在 |
| KeyError | dict キーの typo、存在しないキーアクセス |
| 非同期バグ | await 忘れ、競合状態、コネクション枯渇 |
| 環境差分 | 環境変数未設定、パス差異、バージョン差異 |

## 注意事項
- `print` デバッグは commit 前に必ず除去する
- 「多分こうだろう」で修正しない。必ず検証する

## 検証
修正後にテストが通り、同じ入力で問題が再現しなければ完了。
