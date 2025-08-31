from src.dto.organization import (
    AddUserToOrganizationElement,
    AddUserToOrganizationPayload,
    CreateOrganizationPayload,
    UpdateOrganizationPayload,
)
from src.exceptions import AccessError
from src.models.common import UserAccess
from src.models.organization import OrganizationModel, UserOrganizationModel
from src.use_case.organization import OrganizationUseCase


class OrganizationService:

    def __init__(self, organization_repository: OrganizationUseCase) -> None:
        self.organization_repository = organization_repository

    async def create_organization_by_user(
        self,
        user_id: int,
        payload: CreateOrganizationPayload,
    ) -> OrganizationModel:
        organization_model = await self.organization_repository.create_organization(payload)
        await self.organization_repository.add_users_to_organization(
            AddUserToOrganizationPayload(
                organization_id=organization_model.id,
                users=[
                    AddUserToOrganizationElement(
                        user_id=user_id,
                        access=UserAccess.OWNER,
                    ),
                ],
            ),
        )
        return organization_model

    async def get_user_organizations(self, user_id: int) -> list[UserOrganizationModel]:
        return await self.organization_repository.get_user_organizations(user_id)

    async def update_organization_by_user(
        self,
        user_id: int,
        payload: UpdateOrganizationPayload,
    ) -> OrganizationModel:
        user_access = await self.organization_repository.get_user_access_in_organization(
            user_id,
            payload.organization_id,
        )
        if user_access in (None, UserAccess.PARTIAL):
            raise AccessError(
                21,
                "Access denied",
                "You don't have enough rights to access organization.",
            )

        return await self.organization_repository.update_organization(payload)

