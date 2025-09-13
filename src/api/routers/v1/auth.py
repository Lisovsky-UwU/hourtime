from fastapi import APIRouter, Depends

from src.api.depends import service_user_auth_depends, token_header_scheme
from src.api.handlers import LoggingRoute
from src.dto.api.common import ResultResponse
from src.dto.api.user import UserAuthentificationResponse, UserLoginRequest, UserRegisteringRequest
from src.service.user_auth import UserAuthService

auth_route = APIRouter(prefix="/auth", route_class=LoggingRoute)


@auth_route.post("/registrate")
async def registrate_user(
    resquest_body: UserRegisteringRequest,
    user_auth_service: UserAuthService = Depends(service_user_auth_depends),
) -> UserAuthentificationResponse:
    result = await user_auth_service.registrate_user(resquest_body)
    return UserAuthentificationResponse(
        token=result.token,
    )

@auth_route.post("/login")
async def login_user(
    request_body: UserLoginRequest,
    user_auth_service: UserAuthService = Depends(service_user_auth_depends),
) -> UserAuthentificationResponse:
    result = await user_auth_service.login_user(request_body)
    return UserAuthentificationResponse(
        token=result.token,
    )

@auth_route.post("/logout")
async def logout_user(
    user_auth_service: UserAuthService = Depends(service_user_auth_depends),
    token: str = Depends(token_header_scheme),
) -> ResultResponse:
    await user_auth_service.logout_user(token)
    return ResultResponse()

