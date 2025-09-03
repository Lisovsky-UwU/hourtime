from src.dto.workspace import CreateWorkspacePayload
from src.exceptions import AccessError
from src.models.common import UserAccess
from src.models.workspace import WorkspaceModel
from src.use_case.organization import OrganizationUseCase
from src.use_case.workspace import WorkspaceUseCase


class WorkspaceService:

    def __init__(
        self,
        workspace_repository: WorkspaceUseCase,
        organization_repository: OrganizationUseCase,
    ) -> None:
        self.workspace_repository = workspace_repository
        self.organization_repository = organization_repository

    async def create_workspace(self, payload: CreateWorkspacePayload) -> WorkspaceModel:
        return await self.workspace_repository.create_workspace(payload)

    async def create_workspace_by_user(
        self,
        user_id: int,
        payload: CreateWorkspacePayload,
    ) -> WorkspaceModel:
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

        return await self.create_workspace(payload)

    async def get_by_organization(self, organization_id: int) -> list[WorkspaceModel]:
        return await self.workspace_repository.get_by_organization(organization_id)

