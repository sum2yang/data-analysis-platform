from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthSessionResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    UserProfileResponse,
)
from app.services.auth_service import AuthService

__all__ = ["router"]

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthSessionResponse)
def register(body: RegisterRequest, db=Depends(get_db)):
    svc = AuthService(db)
    return svc.register(
        username=body.username,
        password=body.password,
        display_name=body.display_name,
    )


@router.post("/login", response_model=AuthSessionResponse)
def login(body: LoginRequest, db=Depends(get_db)):
    svc = AuthService(db)
    return svc.authenticate(username=body.username, password=body.password)


@router.post("/refresh", response_model=AuthSessionResponse)
def refresh(body: RefreshRequest, db=Depends(get_db)):
    svc = AuthService(db)
    return svc.rotate_refresh_token(body.refresh_token)


@router.post("/logout", status_code=204)
def logout(body: RefreshRequest, db=Depends(get_db)):
    svc = AuthService(db)
    svc.revoke_refresh_token(body.refresh_token)


@router.get("/me", response_model=UserProfileResponse)
def me(user: User = Depends(get_current_user)):
    return UserProfileResponse.model_validate(user)
