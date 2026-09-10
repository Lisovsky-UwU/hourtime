from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.domain.entities import Project
from hourtime.domain.errors import NotFound
from hourtime.infrastructure.db.models import ProjectModel
from hourtime.infrastructure.db.repositories.integrity import translating_integrity_errors
from hourtime.interfaces.repositories import ProjectRepository


def to_domain(model: ProjectModel) -> Project:
    return Project(
        id=model.id,
        user_id=model.user_id,
        name=model.name,
        color=model.color,
        archived_at=model.archived_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_id: UUID) -> Project | None:
        model = await self._session.get(ProjectModel, project_id)
        return to_domain(model) if model else None

    async def list_for_user(
        self, user_id: UUID, *, include_archived: bool = False
    ) -> list[Project]:
        statement = sa.select(ProjectModel).where(ProjectModel.user_id == user_id)
        if not include_archived:
            statement = statement.where(ProjectModel.archived_at.is_(None))
        statement = statement.order_by(sa.func.lower(ProjectModel.name))
        models = (await self._session.execute(statement)).scalars().all()
        return [to_domain(model) for model in models]

    async def find_by_name(self, user_id: UUID, name: str) -> Project | None:
        statement = sa.select(ProjectModel).where(
            ProjectModel.user_id == user_id,
            sa.func.lower(ProjectModel.name) == name.strip().lower(),
            ProjectModel.archived_at.is_(None),
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return to_domain(model) if model else None

    async def add(self, project: Project) -> Project:
        model = ProjectModel(**project.model_dump())
        self._session.add(model)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def update(self, project: Project) -> Project:
        model = await self._session.get(ProjectModel, project.id)
        if model is None:
            raise NotFound("Project not found")
        for field, value in project.model_dump().items():
            setattr(model, field, value)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def delete(self, project_id: UUID) -> None:
        model = await self._session.get(ProjectModel, project_id)
        if model is None:
            raise NotFound("Project not found")
        await self._session.delete(model)
        await self._session.flush()
