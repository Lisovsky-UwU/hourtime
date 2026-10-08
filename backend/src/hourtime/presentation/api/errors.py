"""Translation of domain errors into HTTP responses.

Every failure the API returns uses the same envelope:

    {"error": {"code": "not_found", "message": "Project not found"}}

so the frontend can branch on `code` and fall back to `message` for display.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from hourtime.domain.errors import (
    AccountDisabled,
    ClientNameTaken,
    DomainError,
    EmailAlreadyUsed,
    InvalidCredentials,
    InvalidCurrentPassword,
    InvalidToken,
    NotFound,
    PermissionDenied,
    ProjectNameTaken,
    RegistrationDisabled,
    TagNameTaken,
    TimerAlreadyRunning,
    ValidationError,
)

# Keyed by plain `type` because lookups walk the MRO, which includes Exception.
_STATUS_BY_ERROR: dict[type, int] = {
    ValidationError: status.HTTP_400_BAD_REQUEST,
    InvalidCurrentPassword: status.HTTP_400_BAD_REQUEST,
    InvalidCredentials: status.HTTP_401_UNAUTHORIZED,
    InvalidToken: status.HTTP_401_UNAUTHORIZED,
    AccountDisabled: status.HTTP_403_FORBIDDEN,
    RegistrationDisabled: status.HTTP_403_FORBIDDEN,
    PermissionDenied: status.HTTP_403_FORBIDDEN,
    NotFound: status.HTTP_404_NOT_FOUND,
    EmailAlreadyUsed: status.HTTP_409_CONFLICT,
    ClientNameTaken: status.HTTP_409_CONFLICT,
    ProjectNameTaken: status.HTTP_409_CONFLICT,
    TagNameTaken: status.HTTP_409_CONFLICT,
    TimerAlreadyRunning: status.HTTP_409_CONFLICT,
}


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


def status_for(error: DomainError) -> int:
    # Walk the MRO so subclasses (SessionExpired -> InvalidToken) inherit a status.
    for klass in type(error).__mro__:
        if klass in _STATUS_BY_ERROR:
            return _STATUS_BY_ERROR[klass]
    return status.HTTP_400_BAD_REQUEST


def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
        headers=headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, error: DomainError) -> JSONResponse:
        return error_response(error.code, error.message, status_for(error))

    @app.exception_handler(RequestValidationError)
    async def _request_validation(_: Request, error: RequestValidationError) -> JSONResponse:
        details = "; ".join(
            f"{'.'.join(str(part) for part in item['loc'][1:]) or 'body'}: {item['msg']}"
            for item in error.errors()
        )
        return error_response(
            "validation_error", details or "Invalid request", status.HTTP_400_BAD_REQUEST
        )
