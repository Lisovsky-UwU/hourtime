from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from hourtime.domain.entities import User
from hourtime.use_cases.dto import SessionTokens


class RegisterRequest(BaseModel):
    email: EmailStr
    # The real length rule comes from HOURTIME_PASSWORD_MIN_LENGTH; this only
    # keeps empty strings out.
    password: str = Field(min_length=1, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_at: datetime
    refresh_expires_at: datetime

    @classmethod
    def of(cls, tokens: SessionTokens) -> "TokenResponse":
        return cls(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            access_expires_at=tokens.access_expires_at,
            refresh_expires_at=tokens.refresh_expires_at,
        )


class UserResponse(BaseModel):
    id: UUID
    email: str
    created_at: datetime

    @classmethod
    def of(cls, user: User) -> "UserResponse":
        return cls(id=user.id, email=user.email, created_at=user.created_at)


class LoginResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse
