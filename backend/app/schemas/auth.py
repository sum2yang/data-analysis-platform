from pydantic import BaseModel, Field

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "RefreshRequest",
    "AuthSessionResponse",
    "UserProfileResponse",
]


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    display_name: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthSessionResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserProfileResponse"


class UserProfileResponse(BaseModel):
    id: str
    username: str
    display_name: str | None
    is_active: bool

    model_config = {"from_attributes": True}
