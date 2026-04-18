---
name: openhue
description: Control Philips Hue smart lights via Hue Bridge REST API
version: 1.0.0
tags: [philips-hue, smart-home, iot, lighting, hue]
category: smart-home
platform: all
triggers: [Hue, Philips Hue, スマートライト, 照明, ライト制御, 電球, smart light, hue bridge]
---

## 使用場面
Philips Hue 電球の ON/OFF、明るさ・色の変更、シーンの設定、自動化の作成。

## Hue Bridge への接続
```python
import httpx

BRIDGE_IP = "192.168.1.100"  # ブリッジの IP (ルーターで確認)
USERNAME = "xxxxxxxxxxxxxxxxxxxx"  # ブリッジで発行した API キー

BASE_URL = f"http://{BRIDGE_IP}/api/{USERNAME}"

# ライト一覧の取得
resp = httpx.get(f"{BASE_URL}/lights")
lights = resp.json()
for id, light in lights.items():
    print(f"ID: {id}, Name: {light['name']}, On: {light['state']['on']}")
```

## API キーの取得
```python
# 1. ブリッジのボタンを押す
# 2. 以下のリクエストを実行
resp = httpx.post(f"http://{BRIDGE_IP}/api", json={
    "devicetype": "openclaw#agent"
})
data = resp.json()
username = data[0]["success"]["username"]
print(f"API Key: {username}")
```

## ライトの制御
```python
def set_light(light_id: str, on: bool = True, bri: int = 254, 
              hue: int = None, sat: int = None) -> dict:
    """ライトの状態を設定"""
    state = {"on": on, "bri": bri, "transitiontime": 4}  # 400ms
    if hue is not None:
        state["hue"] = hue   # 0-65535
    if sat is not None:
        state["sat"] = sat   # 0-254
    
    resp = httpx.put(f"{BASE_URL}/lights/{light_id}/state", json=state)
    return resp.json()

# 電球を ON にして明るさ 50%
set_light("1", on=True, bri=127)

# 赤色に変更
set_light("1", hue=0, sat=254)  # 赤
set_light("1", hue=25500, sat=254)  # 緑
set_light("1", hue=46920, sat=254)  # 青

# 電球を OFF
set_light("1", on=False)
```

## グループ（ルーム）制御
```python
# グループ一覧
groups = httpx.get(f"{BASE_URL}/groups").json()

def set_group(group_id: str, on: bool, bri: int = 254, ct: int = 370) -> dict:
    """グループ全体を制御"""
    state = {"on": on, "bri": bri, "ct": ct}  # ct: 色温度 (153=寒色, 500=暖色)
    resp = httpx.put(f"{BASE_URL}/groups/{group_id}/action", json=state)
    return resp.json()

# リビング全体を読書モードに
set_group("1", on=True, bri=200, ct=300)
```

## シーンの設定
```python
# シーン一覧
scenes = httpx.get(f"{BASE_URL}/scenes").json()

def activate_scene(scene_id: str, group_id: str):
    """シーンを適用"""
    httpx.put(f"{BASE_URL}/groups/{group_id}/action", json={"scene": scene_id})
```

## 自動化スケジュール
```python
# 毎朝 7 時にグループ 1 を ON にするスケジュール
schedule = {
    "name": "Morning Lights",
    "command": {
        "address": f"/api/{USERNAME}/groups/1/action",
        "method": "PUT",
        "body": {"on": True, "bri": 180, "ct": 300}
    },
    "localtime": "W127/T07:00:00"  # 毎日 7:00
}
httpx.post(f"{BASE_URL}/schedules", json=schedule)
```

## 注意事項
- BRIDGE_IP は `arp -a | grep Philips` または Hue アプリで確認
- API キーはブリッジのボタンを押してから 30 秒以内に取得する
- ライト ID は 1 から始まる整数（文字列として渡す）

## 検証
ライトが指定した状態（ON/OFF/色）に変化すれば完了。
