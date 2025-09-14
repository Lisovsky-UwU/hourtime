from fastapi import APIRouter, Depends

from src.api.depends import (
    check_user_token,
    service_organization_depends,
)
from src.api.handlers import LoggingRoute
from src.dto.api.common import ResultResponse
from src.dto.api.organization import CreateOrganizationByUserRequest, UpdateOrganizationRequest
from src.dto.organization import (
    CreateOrganizationPayload,
    UpdateOrganizationPayload,
    UserOrganizationWithWorkspaces,
)
from src.models.organization import OrganizationModel
from src.models.user import UserModel
from src.service.organization import OrganizationService

organization_router = APIRouter(prefix="/organization", route_class=LoggingRoute)


@organization_router.post("/create")
async def create_organization_by_user(
    request_body: CreateOrganizationByUserRequest,
    user_model: UserModel = Depends(check_user_token),
    organization_service: OrganizationService = Depends(service_organization_depends),
) -> OrganizationModel:
    return await organization_service.create_organization_by_user(
        user_model.id,
        CreateOrganizationPayload(
            name=request_body.name,
        ),
    )

@organization_router.get("/my")
async def get_my_organizations(
    user_model: UserModel = Depends(check_user_token),
    organization_service: OrganizationService = Depends(service_organization_depends),
) -> list[UserOrganizationWithWorkspaces]:
    return await organization_service.get_user_organizations(user_model.id)

@organization_router.put("/update")
async def update_my_organization(
    request_body: UpdateOrganizationRequest,
    user_model: UserModel = Depends(check_user_token),
    organization_service: OrganizationService = Depends(service_organization_depends),
) -> OrganizationModel:
    return await organization_service.update_organization_by_user(
        user_model.id,
        UpdateOrganizationPayload(
            organization_id=request_body.organization_id,
            name=request_body.name,
        ),
    )

@organization_router.delete("/delete")
async def delete_my_organization(
    organization_id: int,
    user_model: UserModel = Depends(check_user_token),
    organization_service: OrganizationService = Depends(service_organization_depends),
) -> ResultResponse:
    await organization_service.delete_organization_by_user(
        user_model.id,
        organization_id,
    )
    return ResultResponse()
