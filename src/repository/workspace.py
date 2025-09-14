from sqlalchemy import and_, select

from src.database.converter import DatabaseModelsConverter
from src.database.orm.workspace import WorkspaceORM
from src.dto.workspace import CreateWorkspacePayload, UpdateWorkspacePayload
from src.exceptions import NotFoundError
from src.models.workspace import WorkspaceModel
from src.repository.mixin import DatabaseRepositoryMixin
from src.use_case.workspace import WorkspaceUseCase


class WorkspaceRepositoryDB(DatabaseRepositoryMixin, WorkspaceUseCase):

    async def _get_orm_by_id(self, workspace_id: int, return_deleted: bool = False) -> WorkspaceORM:
        filter_ = WorkspaceORM.id == workspace_id
        if not return_deleted:
            filter_ = and_(filter_, WorkspaceORM.deleted == False)  # noqa: E712

        query = select(WorkspaceORM).filter(filter_)
        result = await self.session.execute(query)
        user_orm = result.scalar()
        if user_orm is None:
            raise NotFoundError(30, "Workspace not found", "Workspace not found in database by id")

        return user_orm

    async def create_workspace(self, payload: CreateWorkspacePayload) -> WorkspaceModel:
        workspace_orm = WorkspaceORM(
            name=payload.name,
            organization_id=payload.organization_id,
        )
        self.session.add(workspace_orm)
        await self.session.commit()
        await self.session.refresh(workspace_orm)
        return DatabaseModelsConverter.workspace_orm_to_model(workspace_orm)

    async def get_by_organization(self, organization_id: int) -> list[WorkspaceModel]:
        query = (
            select(WorkspaceORM)
            .filter(WorkspaceORM.organization_id == organization_id, WorkspaceORM.deleted == False)  # noqa: E712
        )
        result = await self.session.execute(query)
        response: list[WorkspaceModel] = []
        for row in result.scalars():
            response.append(DatabaseModelsConverter.workspace_orm_to_model(row))

        return response

    async def get_workspace_by_id(
        self,
        workspace_id: int,
        return_deleted: bool = False,
    ) -> WorkspaceModel:
        return DatabaseModelsConverter.workspace_orm_to_model(
            await self._get_orm_by_id(workspace_id, return_deleted),
        )

    async def update_workspace(self, payload: UpdateWorkspacePayload) -> WorkspaceModel:
        workspace_orm = await self._get_orm_by_id(payload.workspace_id)
        workspace_orm.name = payload.name
        await self.session.commit()
        await self.session.refresh(workspace_orm)
        return DatabaseModelsConverter.workspace_orm_to_model(workspace_orm)

    async def delete_workspace(self, workspace_id: int) -> None:
        workspace_orm = await self._get_orm_by_id(workspace_id)
        workspace_orm.deleted = True
        await self.session.commit()

