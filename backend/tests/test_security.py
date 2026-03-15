"""Unit tests for JWT token creation/validation and password hashing."""

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"
        assert verify_password("mypassword", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("mypassword")
        assert not verify_password("wrongpassword", hashed)

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # different salts

    def test_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed)
        assert not verify_password("notempty", hashed)


class TestJWT:
    def test_access_token_roundtrip(self):
        token = create_access_token("user-123")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_refresh_token_roundtrip(self):
        token = create_refresh_token("user-456")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"

    def test_expired_token_returns_none(self):
        expired = jwt.encode(
            {"sub": "user-1", "exp": datetime.now(timezone.utc) - timedelta(hours=1), "type": "access"},
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
        assert decode_token(expired) is None

    def test_invalid_token_returns_none(self):
        assert decode_token("garbage.token.here") is None
        assert decode_token("") is None

    def test_tampered_token_returns_none(self):
        token = create_access_token("user-1")
        tampered = token[:-5] + "XXXXX"
        assert decode_token(tampered) is None

    def test_wrong_secret_returns_none(self):
        token = jwt.encode(
            {"sub": "user-1", "exp": datetime.now(timezone.utc) + timedelta(hours=1), "type": "access"},
            "wrong-secret",
            algorithm="HS256",
        )
        assert decode_token(token) is None

    def test_access_token_has_expiry(self):
        token = create_access_token("user-1")
        payload = decode_token(token)
        assert "exp" in payload
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        # Should expire within ~15 minutes
        assert exp - datetime.now(timezone.utc) < timedelta(minutes=16)
