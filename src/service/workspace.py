from src.dto.workspace import CreateWorkspacePayload, UpdateWorkspacePayload
from src.exceptions import AccessError, LogicalError, NotFoundError
from src.models.common import UserAccess
from src.models.workspace import WorkspaceModel
from src.use_case.organization import OrganizationUseCase
from src.use_case.workspace import WorkspaceUseCase


class WorkspaceService:

    _access_organization_error = AccessError(
        21,
        "Access denied",
        "You don't have enough rights to access organization.",
    )

    def __init__(
        self,
        workspace_repository: WorkspaceUseCase,
        organization_repository: OrganizationUseCase,
    ) -> None:
        self.workspace_repository = workspace_repository
        self.organization_repository = organization_repository

    async def _check_user_access(
        self,
        user_id: int,
        *,
        workspace_id: int | None = None,
        organization_id: int | None = None,
    ) -> None:
        """
        Must have one of the parameter: `workspace_id` or `organization_id`.
        """
        if workspace_id is None and organization_id is None:
            raise LogicalError(
                501,
                "Parameters for _check_user_access error",
                "None of the parameters were passed: workspace_id or organization_id",
            )

        if organization_id is None:
            try:
                workspace_model = await self.workspace_repository.get_workspace_by_id(
                    workspace_id, # type: ignore
                )
                organization_id = workspace_model.organization_id
            except NotFoundError as exc:
                raise self._access_organization_error from exc

        user_access = await self.organization_repository.get_user_access_in_organization(
            user_id,
            organization_id,
        )
        if user_access in (None, UserAccess.PARTIAL):
            raise self._access_organization_error

    async def create_workspace(self, payload: CreateWorkspacePayload) -> WorkspaceModel:
        return await self.workspace_repository.create_workspace(payload)

    async def create_workspace_by_user(
        self,
        user_id: int,
        payload: CreateWorkspacePayload,
    ) -> WorkspaceModel:
        await self._check_user_access(user_id, organization_id=payload.organization_id)
        return await self.create_workspace(payload)

    async def get_by_organization(self, organization_id: int) -> list[WorkspaceModel]:
        return await self.workspace_repository.get_by_organization(organization_id)

    async def update_workspace_by_user(
        self,
        user_id: int,
        payload: UpdateWorkspacePayload,
    ) -> WorkspaceModel:
        await self._check_user_access(user_id, workspace_id=payload.workspace_id)
        return await self.workspace_repository.update_workspace(payload)

    async def delete_workspace_by_user(self, user_id: int, workspace_id: int,) -> None:
        await self._check_user_access(user_id, workspace_id=workspace_id)
        await self.workspace_repository.delete_workspace(workspace_id)

