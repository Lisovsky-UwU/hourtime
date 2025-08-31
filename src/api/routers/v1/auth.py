from fastapi import APIRouter, Depends

from src.api.depends import check_authorization_token, service_user_auth_depends
from src.api.handlers import LoggingRoute
from src.dto.api.user import UserAuthentificationResponse, UserLoginRequest, UserRegisteringRequest
from src.models.user import UserModel
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
        user_data=result.user,
    )

@auth_route.post("/login")
async def login_user(
    request_body: UserLoginRequest,
    user_auth_service: UserAuthService = Depends(service_user_auth_depends),
) -> UserAuthentificationResponse:
    result = await user_auth_service.login_user(request_body)
    return UserAuthentificationResponse(
        token=result.token,
        user_data=result.user,
    )

@auth_route.get("/check_auth")
async def check_auth_user(user_model: UserModel = Depends(check_authorization_token)) -> UserModel:
    return user_model

