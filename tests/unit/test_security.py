from datetime import timedelta

import jwt
import pytest

from app.core.security import (
    ACCESS_TOKEN_TYPE,
    _create_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

DEFAULT_PASSWORD = "password123"


def test_verify_password_accepts_correct_password() -> None:
    hashed = hash_password(DEFAULT_PASSWORD)

    assert verify_password(DEFAULT_PASSWORD, hashed) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password(DEFAULT_PASSWORD)
    assert verify_password("wrong-password", hashed) is False


def test_hash_is_not_the_plain_password() -> None:
    hashed = hash_password(DEFAULT_PASSWORD)

    assert hashed != DEFAULT_PASSWORD


def test_same_password_hashes_differently() -> None:
    first = hash_password(DEFAULT_PASSWORD)
    second = hash_password(DEFAULT_PASSWORD)

    assert first != second


def test_access_token_carries_user_id() -> None:
    token = create_access_token(37)
    payload = decode_token(token, ACCESS_TOKEN_TYPE)
    assert payload["sub"] == "37"


def test_refresh_token_is_rejected_as_access_token() -> None:
    refresh = create_refresh_token(37)
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(refresh, ACCESS_TOKEN_TYPE)


def test_expired_token_is_rejected() -> None:
    token = _create_token(37, ACCESS_TOKEN_TYPE, timedelta(minutes=-1))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token, ACCESS_TOKEN_TYPE)
