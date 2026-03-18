from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    avatar_url: str | None = None
    credit_balance: int
    daily_credit_limit: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    avatar_url: str | None = Field(None, max_length=500)
    daily_credit_limit: int | None = Field(None, ge=0, le=1000000)

    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return v
        if not v.startswith(("https://", "http://")):
            raise ValueError("Avatar URL must start with https:// or http://")
        return v
