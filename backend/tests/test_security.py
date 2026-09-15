"""Regression tests for Phase 02 security helpers."""

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    password = "Phase02-Test-Password!"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_refresh_tokens_are_unique_and_decodable() -> None:
    first = create_refresh_token("user-1", "org-1", "ADMIN")
    second = create_refresh_token("user-1", "org-1", "ADMIN")

    assert first != second

    first_payload = decode_refresh_token(first)
    second_payload = decode_refresh_token(second)

    assert first_payload["type"] == "refresh"
    assert second_payload["type"] == "refresh"
    assert first_payload["jti"] != second_payload["jti"]
