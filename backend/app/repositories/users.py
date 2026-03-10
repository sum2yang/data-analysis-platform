from sqlalchemy.orm import Session

from app.models.user import User

__all__ = ["UserRepository"]


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, username: str, hashed_password: str, display_name: str | None = None) -> User:
        user = User(
            username=username,
            hashed_password=hashed_password,
            display_name=display_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()
