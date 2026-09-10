from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from hourtime.presentation.api.deps import (
    AccessTokenDep,
    CurrentUserDep,
    get_login_user,
    get_logout_user,
    get_refresh_session,
    get_register_user,
)
from hourtime.presentation.api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from hourtime.use_cases.auth import LoginUser, LogoutUser, RefreshSession, RegisterUser
from hourtime.use_cases.dto import LoginUserInput, RefreshSessionInput, RegisterUserInput

router = APIRouter(prefix="/auth", tags=["auth"])

USER_AGENT_MAX_LENGTH = 512


def _client_hints(request: Request) -> tuple[str | None, str | None]:
    """User agent and IP recorded on the session, for future session management."""
    user_agent = request.headers.get("user-agent")
    if user_agent is not None:
        user_agent = user_agent[:USER_AGENT_MAX_LENGTH]
    ip = request.client.host if request.client else None
    return user_agent, ip


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    use_case: Annotated[RegisterUser, Depends(get_register_user)],
) -> UserResponse:
    user = await use_case.execute(RegisterUserInput(email=body.email, password=body.password))
    return UserResponse.of(user)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    use_case: Annotated[LoginUser, Depends(get_login_user)],
) -> LoginResponse:
    user_agent, ip = _client_hints(request)
    result = await use_case.execute(
        LoginUserInput(email=body.email, password=body.password, user_agent=user_agent, ip=ip)
    )
    return LoginResponse(user=UserResponse.of(result.user), tokens=TokenResponse.of(result.tokens))


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    body: RefreshRequest,
    request: Request,
    use_case: Annotated[RefreshSession, Depends(get_refresh_session)],
) -> LoginResponse:
    user_agent, ip = _client_hints(request)
    result = await use_case.execute(
        RefreshSessionInput(refresh_token=body.refresh_token, user_agent=user_agent, ip=ip)
    )
    return LoginResponse(user=UserResponse.of(result.user), tokens=TokenResponse.of(result.tokens))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    access_token: AccessTokenDep,
    use_case: Annotated[LogoutUser, Depends(get_logout_user)],
) -> Response:
    await use_case.execute(access_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    current: CurrentUserDep,
    use_case: Annotated[LogoutUser, Depends(get_logout_user)],
) -> Response:
    await use_case.execute_all(current.user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def me(current: CurrentUserDep) -> UserResponse:
    return UserResponse.of(current.user)
