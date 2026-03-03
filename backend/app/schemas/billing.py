from datetime import datetime

from pydantic import BaseModel


class CreditsResponse(BaseModel):
    balance: int
    used_this_period: int
    plan: str


class CreditTransactionResponse(BaseModel):
    id: str
    amount: int
    balance_after: int
    reason: str
    model_name: str | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlanResponse(BaseModel):
    id: str
    name: str
    price_monthly: float
    credits_included: int
    max_agents: int


class CheckoutRequest(BaseModel):
    plan: str  # starter, pro, business


class CheckoutResponse(BaseModel):
    checkout_url: str


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    tier: str  # standard or premium
    credits_per_1k_input: float
    credits_per_1k_output: float
    description: str
