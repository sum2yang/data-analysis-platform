import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.auth import AuthSessionResponse, UserProfileResponse

__all__ = ["AuthService"]


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(
        self, *, username: str, password: str, display_name: str | None = None
    ) -> AuthSessionResponse:
        existing = self.user_repo.get_by_username(username)
        if existing:
            raise ConflictError("Username already exists")

        user = self.user_repo.create(
            username=username,
            hashed_password=hash_password(password),
            display_name=display_name,
        )
        return self._create_session(user)

    def authenticate(self, *, username: str, password: str) -> AuthSessionResponse:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")
        if not user.is_active:
            raise AuthenticationError("Account is disabled")
        return self._create_session(user)

    def rotate_refresh_token(self, raw_token: str) -> AuthSessionResponse:
        token_hash = self._hash_token(raw_token)
        record = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,  # noqa: E712
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )
        if not record:
            raise AuthenticationError("Invalid or expired refresh token")

        record.revoked = True
        user = self.user_repo.get_by_id(record.user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or disabled")

        session = self._create_session(user)
        self.db.commit()
        return session

    def revoke_refresh_token(self, raw_token: str) -> None:
        token_hash = self._hash_token(raw_token)
        record = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )
        if record:
            record.revoked = True
            self.db.commit()

    def _create_session(self, user: User) -> AuthSessionResponse:
        access = create_access_token(user.id)
        refresh = create_refresh_token(user.id)
        self._store_refresh_token(user.id, refresh)
        return AuthSessionResponse(
            access_token=access,
            refresh_token=refresh,
            user=UserProfileResponse.model_validate(user),
        )

    def _store_refresh_token(self, user_id: str, raw_token: str) -> None:
        settings = get_settings()
        record = RefreshToken(
            user_id=user_id,
            token_hash=self._hash_token(raw_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(record)
        self.db.commit()

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()
