from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.errors import AuthenticationError, ConflictError
from app.models.refresh_token import RefreshToken
from app.repositories.users import UserRepository
from app.services.auth_service import AuthService


def test_register_creates_user_and_returns_session(db_session):
    svc = AuthService(db_session)
    session = svc.register(username="alice", password="password123", display_name="Alice")

    assert session.user.username == "alice"
    assert session.access_token
    assert session.refresh_token

    user = UserRepository(db_session).get_by_username("alice")
    assert user is not None
    tokens = db_session.query(RefreshToken).filter(RefreshToken.user_id == user.id).all()
    assert len(tokens) == 1
    assert tokens[0].revoked is False


def test_register_raises_conflict_error_on_duplicate_username(db_session):
    svc = AuthService(db_session)
    svc.register(username="alice", password="password123")

    with pytest.raises(ConflictError):
        svc.register(username="alice", password="password456")


def test_authenticate_succeeds_with_correct_credentials(db_session):
    svc = AuthService(db_session)
    svc.register(username="alice", password="password123")

    session = svc.authenticate(username="alice", password="password123")
    assert session.user.username == "alice"
    assert session.access_token
    assert session.refresh_token


def test_authenticate_fails_with_wrong_password(db_session):
    svc = AuthService(db_session)
    svc.register(username="alice", password="password123")

    with pytest.raises(AuthenticationError):
        svc.authenticate(username="alice", password="wrong")


def test_authenticate_fails_with_non_existent_user(db_session):
    svc = AuthService(db_session)

    with pytest.raises(AuthenticationError):
        svc.authenticate(username="missing", password="password123")


def test_authenticate_fails_with_inactive_user(db_session):
    svc = AuthService(db_session)
    svc.register(username="alice", password="password123")
    user = UserRepository(db_session).get_by_username("alice")
    assert user is not None
    user.is_active = False
    db_session.commit()

    with pytest.raises(AuthenticationError):
        svc.authenticate(username="alice", password="password123")


def test_rotate_refresh_token_works_with_valid_token(db_session):
    svc = AuthService(db_session)
    session1 = svc.register(username="alice", password="password123")
    old_refresh = session1.refresh_token

    session2 = svc.rotate_refresh_token(old_refresh)
    assert session2.refresh_token != old_refresh

    old_hash = svc._hash_token(old_refresh)
    old_record = (
        db_session.query(RefreshToken).filter(RefreshToken.token_hash == old_hash).first()
    )
    assert old_record is not None
    assert old_record.revoked is True

    new_hash = svc._hash_token(session2.refresh_token)
    new_record = (
        db_session.query(RefreshToken).filter(RefreshToken.token_hash == new_hash).first()
    )
    assert new_record is not None
    assert new_record.revoked is False


def test_rotate_refresh_token_fails_with_revoked_token(db_session):
    svc = AuthService(db_session)
    session = svc.register(username="alice", password="password123")
    raw = session.refresh_token

    token_hash = svc._hash_token(raw)
    record = db_session.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    assert record is not None
    record.revoked = True
    db_session.commit()

    with pytest.raises(AuthenticationError):
        svc.rotate_refresh_token(raw)


def test_rotate_refresh_token_fails_with_expired_token(db_session):
    svc = AuthService(db_session)
    session = svc.register(username="alice", password="password123")
    raw = session.refresh_token

    token_hash = svc._hash_token(raw)
    record = db_session.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    assert record is not None
    record.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    with pytest.raises(AuthenticationError):
        svc.rotate_refresh_token(raw)


def test_revoke_refresh_token_revokes_the_token(db_session):
    svc = AuthService(db_session)
    session = svc.register(username="alice", password="password123")
    raw = session.refresh_token

    svc.revoke_refresh_token(raw)

    token_hash = svc._hash_token(raw)
    record = db_session.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    assert record is not None
    assert record.revoked is True
