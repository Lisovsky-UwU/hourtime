from fastapi import APIRouter, Depends

from src.api.depends import (
    check_user_token,
    service_user_auth_depends,
    service_user_depends,
)
from src.api.handlers import LoggingRoute
from src.dto.api.common import ResultResponse
from src.dto.api.user import ChangeUserPasswordRequest, UpdateUserRequest
from src.models.user import UserModel
from src.service.user import UserService
from src.service.user_auth import UserAuthService

user_route = APIRouter(prefix="/user", route_class=LoggingRoute)


@user_route.get("/me/info")
async def get_my_user_info(
    user_model: UserModel = Depends(check_user_token),
) -> UserModel:
    return user_model


@user_route.put("/me/update")
async def update_user_data(
    request_body: UpdateUserRequest,
    user_model: UserModel = Depends(check_user_token),
    user_service: UserService = Depends(service_user_depends),
) -> UserModel:
    new_user_model = await user_service.update_user_data(
        user_id=user_model.id,
        payload=request_body,
    )
    return new_user_model


@user_route.put("/me/change_password")
async def change_user_password(
    request_body: ChangeUserPasswordRequest,
    user_model: UserModel = Depends(check_user_token),
    auth_user_service: UserAuthService = Depends(service_user_auth_depends),
) -> ResultResponse:
    await auth_user_service.change_user_password(
        user_id=user_model.id,
        payload=request_body,
    )
    return ResultResponse()

@user_route.delete("/me/delete")
async def delete_user_by_himself(
    user_model: UserModel = Depends(check_user_token),
    user_service: UserService = Depends(service_user_depends),
) -> ResultResponse:
    await user_service.delete_user(user_model.id)
    return ResultResponse()

