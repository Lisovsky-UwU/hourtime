from src.dto.project import CreateProjectPayload, UpdateProjectPayload
from src.exceptions.defined import ORGANIZATION_ACCESS_ERROR
from src.exceptions.types import NotFoundError
from src.models.common import UserAccess
from src.models.project import ProjectModel
from src.use_case.project import ProjectUseCase
from src.use_case.workspace import WorkspaceUseCase


class ProjectService:

    def __init__(self, project_repository: ProjectUseCase, workspace_repository: WorkspaceUseCase):
        self.project_repository = project_repository
        self.workspace_repository = workspace_repository

    async def _check_access_to_workspace(self, user_id: int, workspace_id: int) -> None:
        user_access = await self.workspace_repository.get_user_access(
            user_id,
            workspace_id,
        )
        if user_access in (None, UserAccess.PARTIAL):
            raise ORGANIZATION_ACCESS_ERROR

    async def _check_access_to_project(self, user_id: int, project_id: int) -> None:
        try:
            project_model = await self.project_repository.get_by_id(project_id)
        except NotFoundError as exc:
            raise ORGANIZATION_ACCESS_ERROR from exc

        await self._check_access_to_workspace(user_id, project_model.workspace_id)

    async def create_by_user(self, user_id: int, payload: CreateProjectPayload) -> ProjectModel:
        await self._check_access_to_workspace(user_id, payload.workspace_id)
        return await self.project_repository.create_project(payload)

    async def get_by_user_for_workspace(
        self,
        user_id: int,
        workspace_id: int,
    ) -> list[ProjectModel]:
        await self._check_access_to_workspace(user_id, workspace_id)
        return await self.project_repository.get_by_workspace(workspace_id)

    async def update_by_user(self, user_id: int, payload: UpdateProjectPayload) -> ProjectModel:
        await self._check_access_to_project(user_id, payload.project_id)
        return await self.project_repository.update_project(payload)

    async def delete_by_user(self, user_id: int, project_id: int) -> None:
        await self._check_access_to_project(user_id, project_id)
        await self.project_repository.delete_project(project_id)

