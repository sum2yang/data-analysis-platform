from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_returns_a_bcrypt_hash():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert hashed.startswith("$2")


def test_verify_password_succeeds_with_correct_password():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_password_fails_with_wrong_password():
    hashed = hash_password("secret123")
    assert verify_password("wrong", hashed) is False


def test_create_access_token_returns_valid_jwt(test_settings):
    token = create_access_token("user-123")
    payload = jwt.decode(
        token,
        test_settings.JWT_SECRET_KEY,
        algorithms=[test_settings.JWT_ALGORITHM],
    )
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert "exp" in payload
    uuid.UUID(payload["jti"])


def test_create_refresh_token_returns_valid_jwt(test_settings):
    token = create_refresh_token("user-123")
    payload = jwt.decode(
        token,
        test_settings.JWT_SECRET_KEY,
        algorithms=[test_settings.JWT_ALGORITHM],
    )
    assert payload["sub"] == "user-123"
    assert payload["type"] == "refresh"
    assert "exp" in payload
    uuid.UUID(payload["jti"])


def test_decode_access_token_decodes_correctly():
    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_decode_access_token_raises_on_expired_token(test_settings):
    exp = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = jwt.encode(
        {"sub": "user-123", "exp": exp, "type": "access", "jti": str(uuid.uuid4())},
        test_settings.JWT_SECRET_KEY,
        algorithm=test_settings.JWT_ALGORITHM,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_decode_access_token_raises_on_invalid_token():
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("not-a-jwt")
