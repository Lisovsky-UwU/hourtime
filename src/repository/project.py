from sqlalchemy import and_, select

from src.database.converter import DatabaseModelsConverter
from src.database.orm.project import ProjectORM
from src.dto.project import CreateProjectPayload, UpdateProjectPayload
from src.exceptions import NotFoundError
from src.models.project import ProjectModel
from src.repository.mixin import DatabaseRepositoryMixin
from src.use_case.project import ProjectUseCase


class ProjectRepositoryDB(DatabaseRepositoryMixin, ProjectUseCase):

    async def _get_orm_by_id(self, project_id: int, return_deleted: bool = False) -> ProjectORM:
        filter_ = ProjectORM.id == project_id
        if not return_deleted:
            filter_ = and_(filter_, ProjectORM.deleted == False)  # noqa: E712

        query = select(ProjectORM).filter(filter_)

        result = await self.session.execute(query)
        user_orm = result.scalar()
        if user_orm is None:
            raise NotFoundError(40, "Project not found", "Project not found in database by id")

        return user_orm

    async def create_project(self, payload: CreateProjectPayload) -> ProjectModel:
        project_orm = ProjectORM(
            workspace_id=payload.workspace_id,
            name=payload.name,
            description=payload.description,
        )
        self.session.add(project_orm)
        await self.session.commit()
        await self.session.refresh(project_orm)
        return DatabaseModelsConverter.project_orm_to_model(project_orm)

    async def get_by_id(self, project_id: int, return_deleted: bool = False) -> ProjectModel:
        return DatabaseModelsConverter.project_orm_to_model(
            await self._get_orm_by_id(project_id, return_deleted),
        )

    async def get_by_workspace(self, workspace_id: int) -> list[ProjectModel]:
        query = select(ProjectORM).filter_by(workspace_id=workspace_id, deleted=False)

        result = await self.session.execute(query)
        response: list[ProjectModel] = []
        for row in result.scalars():
            response.append(DatabaseModelsConverter.project_orm_to_model(row))

        return response

    async def update_project(self, payload: UpdateProjectPayload) -> ProjectModel:
        project_orm = await self._get_orm_by_id(payload.project_id)
        project_orm.name = payload.name
        project_orm.description = payload.description
        await self.session.commit()
        await self.session.refresh(project_orm)
        return DatabaseModelsConverter.project_orm_to_model(project_orm)

    async def delete_project(self, project_id: int) -> None:
        project_orm = await self._get_orm_by_id(project_id)
        project_orm.deleted = True
        await self.session.commit()

