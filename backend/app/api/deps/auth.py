from fastapi import Depends, Header

from app.core.errors import AuthenticationError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.users import UserRepository

__all__ = ["get_current_user"]


def get_current_user(
    authorization: str | None = Header(None),
    db=Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid authorization header")

    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_access_token(token)
    except Exception:
        raise AuthenticationError("Invalid or expired token")

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User not found or disabled")

    return user
