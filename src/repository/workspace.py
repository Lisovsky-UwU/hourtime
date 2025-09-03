from sqlalchemy import select

from src.database.converter import DatabaseModelsConverter
from src.database.orm.workspace import WorkspaceORM
from src.dto.workspace import CreateWorkspacePayload
from src.models.workspace import WorkspaceModel
from src.repository.mixin import DatabaseRepositoryMixin
from src.use_case.workspace import WorkspaceUseCase


class WorkspaceRepositoryDB(DatabaseRepositoryMixin, WorkspaceUseCase):

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

