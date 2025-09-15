from src.dto.workspace import (
    CreateWorkspacePayload,
    UpdateWorkspacePayload,
    WorkspaceListWithAccess,
    WorkspaceSubElement,
)
from src.exceptions import NotFoundError
from src.exceptions.defined import ORGANIZATION_ACCESS_ERROR
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

    async def _check_user_access_for_workspace(
        self,
        user_id: int,
        workspace_id: int,
    ) -> UserAccess:
        user_access = await self.workspace_repository.get_user_access(
            user_id,
            workspace_id,
        )
        if user_access in (None, UserAccess.PARTIAL):
            raise ORGANIZATION_ACCESS_ERROR

        return user_access

    async def create_workspace(self, payload: CreateWorkspacePayload) -> WorkspaceModel:
        return await self.workspace_repository.create_workspace(payload)

    async def create_workspace_by_user(
        self,
        user_id: int,
        payload: CreateWorkspacePayload,
    ) -> WorkspaceModel:
        try:
            user_access = await self.organization_repository.get_user_access_in_organization(
                user_id,
                payload.organization_id,
            )
        except NotFoundError as exc:
            raise ORGANIZATION_ACCESS_ERROR from exc

        if user_access in (None, UserAccess.PARTIAL):
            raise ORGANIZATION_ACCESS_ERROR

        return await self.create_workspace(payload)

    async def get_by_organization_from_user(
        self,
        user_id: int,
        organization_id: int,
    ) -> WorkspaceListWithAccess:
        try:
            user_access = await self.organization_repository.get_user_access_in_organization(
                user_id,
                organization_id,
            )
        except NotFoundError as exc:
            raise ORGANIZATION_ACCESS_ERROR from exc

        if user_access is None:
            raise ORGANIZATION_ACCESS_ERROR

        workspaces = await self.workspace_repository.get_by_organization(organization_id)
        return WorkspaceListWithAccess(
            access=user_access,
            workspaces=[
                WorkspaceSubElement(
                    id=workspace.id,
                    name=workspace.name,
                ) for workspace in workspaces
            ],
        )

    async def update_workspace_by_user(
        self,
        user_id: int,
        payload: UpdateWorkspacePayload,
    ) -> WorkspaceModel:
        await self._check_user_access_for_workspace(user_id, payload.workspace_id)
        return await self.workspace_repository.update_workspace(payload)

    async def delete_workspace_by_user(self, user_id: int, workspace_id: int,) -> None:
        await self._check_user_access_for_workspace(user_id, workspace_id=workspace_id)
        await self.workspace_repository.delete_workspace(workspace_id)

