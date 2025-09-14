from src.dto.organization import (
    AddUserToOrganizationElement,
    AddUserToOrganizationPayload,
    CreateOrganizationPayload,
    UpdateOrganizationPayload,
    UserOrganizationWithWorkspaces,
)
from src.dto.workspace import CreateWorkspacePayload
from src.exceptions.defined import ORGANIZATION_ACCESS_ERROR
from src.models.common import UserAccess
from src.models.organization import OrganizationModel
from src.use_case.organization import OrganizationUseCase
from src.use_case.workspace import WorkspaceUseCase


class OrganizationService:

    def __init__(
        self,
        organization_repository: OrganizationUseCase,
        workspace_repository: WorkspaceUseCase,
    ) -> None:
        self.organization_repository = organization_repository
        self.workspace_repository = workspace_repository

    async def _check_user_access(self, user_id: int, organization_id: int) -> None:
        user_access = await self.organization_repository.get_user_access_in_organization(
            user_id,
            organization_id,
        )
        if user_access in (None, UserAccess.PARTIAL):
            raise ORGANIZATION_ACCESS_ERROR

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
        await self.workspace_repository.create_workspace(
            CreateWorkspacePayload(
                organization_id=organization_model.id,
                name="Default",
            ),
        )
        return organization_model

    async def get_user_organizations(self, user_id: int) -> list[UserOrganizationWithWorkspaces]:
        return await self.organization_repository.get_user_organizations(user_id)

    async def update_organization(self, payload: UpdateOrganizationPayload) -> OrganizationModel:
        return await self.organization_repository.update_organization(payload)

    async def update_organization_by_user(
        self,
        user_id: int,
        payload: UpdateOrganizationPayload,
    ) -> OrganizationModel:
        await self._check_user_access(user_id, payload.organization_id)
        return await self.update_organization(payload)

    async def delete_organization_by_user(
        self,
        user_id: int,
        organization_id: int,
    ) -> None:
        await self._check_user_access(user_id, organization_id)
        await self.organization_repository.delete_organization(organization_id)

