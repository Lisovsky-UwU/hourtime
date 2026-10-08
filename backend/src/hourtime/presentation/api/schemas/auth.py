from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from hourtime.domain.entities import User
from hourtime.domain.entities.user import (
    DISPLAY_NAME_MAX_LENGTH,
    TIMEZONE_MAX_LENGTH,
    DurationFormat,
    HourCycle,
)
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
    display_name: str | None
    # Null until a client reports its zone; consumers fall back to UTC.
    timezone: str | None
    week_start: int
    duration_format: DurationFormat
    hour_cycle: HourCycle
    created_at: datetime

    @classmethod
    def of(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            timezone=user.timezone,
            week_start=user.week_start,
            duration_format=user.duration_format,
            hour_cycle=user.hour_cycle,
            created_at=user.created_at,
        )


class UpdateProfileRequest(BaseModel):
    """Omitted fields are left untouched; `display_name: null` clears the name."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, max_length=DISPLAY_NAME_MAX_LENGTH)
    timezone: str | None = Field(default=None, max_length=TIMEZONE_MAX_LENGTH)
    week_start: int | None = Field(default=None, ge=0, le=6)
    duration_format: DurationFormat | None = None
    hour_cycle: HourCycle | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    # The real length rule comes from HOURTIME_PASSWORD_MIN_LENGTH, as on register.
    new_password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse
