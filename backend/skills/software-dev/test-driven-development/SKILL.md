---
name: test-driven-development
description: Red-Green-Refactor cycle for writing tests before implementation
version: 1.0.0
tags: [tdd, testing, test, pytest, jest, unit-test]
category: software-dev
platform: all
triggers: [TDD, テスト駆動, test driven, write tests, テスト作成, unit test, テスト, pytest, jest]
---

## 使用場面
新機能の実装前にテストを書く、既存コードのテストカバレッジを上げる、リファクタリング安全網を作る。

## Red-Green-Refactor サイクル

### Step 1: Red — 失敗するテストを書く
```python
def test_calculate_discount_applies_10_percent():
    result = calculate_discount(price=100, rate=0.10)
    assert result == 90  # 実装前なので NameError または失敗
```
- まだ実装しない。テストが失敗することを確認する
- テスト名は「何を・どう・期待するか」を明示する

### Step 2: Green — 最小限の実装でテストを通す
```python
def calculate_discount(price: float, rate: float) -> float:
    return price * (1 - rate)
```
- YAGNI：テストを通す最小コードのみ書く
- 綺麗さより動作優先

### Step 3: Refactor — 動作を保ちつつ改善
- 重複を除去、命名改善、パフォーマンス最適化
- 各リファクタリング後にテストを再実行する

## テスト構造 (AAA パターン)
```python
def test_feature():
    # Arrange: テスト用データ準備
    user = User(name="田中", credits=500)
    
    # Act: テスト対象を実行
    result = user.deduct_credits(100)
    
    # Assert: 期待値と比較
    assert result is True
    assert user.credits == 400
```

## カバレッジ目標
- 新機能: 90% 以上
- クリティカルパス（認証・決済）: 100%
- `pytest --cov=app --cov-report=term-missing` で確認

## 注意事項
- テストは独立させる（他のテストの結果に依存しない）
- モックは外部依存（DB・API・ファイル）のみに使用
- フレイキーテスト（不安定）はすぐ修正する

## 検証
`pytest -v` がすべて GREEN で通れば完了。
