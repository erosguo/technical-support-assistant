"""Auth service tests — Phase 2 Task 2.1 (password) + Task 2.2 (JWT)."""

import pytest


class TestPasswordHash:
    def test_hash_password_returns_hash(self):
        from app.services.auth import hash_password

        result = hash_password("mysecret")
        assert result != "mysecret"
        assert result.startswith("$2b$")

    def test_hash_password_different_each_time(self):
        from app.services.auth import hash_password

        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt uses random salt

    def test_verify_password_correct(self):
        from app.services.auth import hash_password, verify_password

        hashed = hash_password("correctpass")
        assert verify_password("correctpass", hashed) is True

    def test_verify_password_wrong(self):
        from app.services.auth import hash_password, verify_password

        hashed = hash_password("correctpass")
        assert verify_password("wrongpass", hashed) is False


class TestJWTToken:
    def test_create_access_token_returns_string(self):
        from app.services.auth import create_access_token

        token = create_access_token({"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token_valid(self):
        from app.services.auth import create_access_token, decode_token

        token = create_access_token({"sub": "user-123", "role": "admin"})
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["role"] == "admin"

    def test_decode_token_expired_raises(self):
        from app.services.auth import create_access_token, decode_token

        token = create_access_token({"sub": "user-123"}, expires_minutes=-1)
        with pytest.raises(Exception):
            decode_token(token)

    def test_decode_token_invalid_raises(self):
        from app.services.auth import decode_token

        with pytest.raises(Exception):
            decode_token("invalid.token.here")
