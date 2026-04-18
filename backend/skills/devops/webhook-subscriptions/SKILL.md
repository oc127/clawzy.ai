---
name: webhook-subscriptions
description: Set up, receive, and process webhook events from external services
version: 1.0.0
tags: [webhook, devops, integration, events, http]
category: devops
platform: all
triggers: [webhook, ウェブフック, event, イベント, subscription, サブスクリプション, HTTP callback, 通知受信]
---

## 使用場面
GitHub・Stripe・Slack からのイベント受信、CI/CD トリガー、サービス間のリアルタイム連携。

## FastAPI で Webhook 受信エンドポイント
```python
from fastapi import APIRouter, Request, Header, HTTPException
import hashlib
import hmac

router = APIRouter()

WEBHOOK_SECRET = "whsec_xxxxxxxxxxxx"

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """HMAC-SHA256 署名を検証"""
    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@router.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_hub_signature_256: str = Header(...),
):
    payload = await request.body()
    
    if not verify_signature(payload, x_hub_signature_256, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = await request.json()
    
    if x_github_event == "push":
        branch = data["ref"].split("/")[-1]
        commits = len(data["commits"])
        print(f"Push to {branch}: {commits} commits")
    
    elif x_github_event == "pull_request":
        action = data["action"]
        pr_title = data["pull_request"]["title"]
        print(f"PR {action}: {pr_title}")
    
    return {"status": "ok"}
```

## Stripe Webhook
```python
import stripe

stripe.api_key = "sk_live_xxxx"

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(...),
):
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, "whsec_xxxxx"
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        amount = pi["amount"] / 100
        print(f"Payment succeeded: ¥{amount:,.0f}")
    
    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        print(f"Subscription cancelled: {sub['customer']}")
    
    return {"received": True}
```

## ローカル開発用（ngrok）
```bash
# ngrok で外部公開
ngrok http 8000

# 発行される URL を Webhook 設定に登録
# https://xxxx.ngrok.io/webhooks/github
```

## Webhook の冪等性（重複処理防止）
```python
import redis

redis_client = redis.Redis()
EXPIRY = 3600  # 1 時間

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(...)):
    data = await request.json()
    event_id = data.get("id", "")
    
    # 重複チェック
    if redis_client.get(f"webhook:{event_id}"):
        return {"status": "duplicate, skipped"}
    
    redis_client.setex(f"webhook:{event_id}", EXPIRY, "1")
    
    # 処理...
    return {"status": "processed"}
```

## 注意事項
- 必ず署名を検証する（セキュリティ上重要）
- Webhook は 5 秒以内に 200 を返す（重い処理はバックグラウンドで）
- 冪等性を実装する（再送による重複処理を防ぐ）

## 検証
Webhook を受信して署名検証が通り、イベントが処理されれば完了。
