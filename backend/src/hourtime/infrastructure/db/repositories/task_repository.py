from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.domain.entities import Task
from hourtime.domain.errors import TaskNotFound
from hourtime.infrastructure.db.models import ProjectModel, TaskModel
from hourtime.infrastructure.db.repositories.integrity import translating_integrity_errors
from hourtime.interfaces.repositories import TaskRepository


def to_domain(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        project_id=model.project_id,
        name=model.name,
        estimated_seconds=model.estimated_seconds,
        completed_at=model.completed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlTaskRepository(TaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, task_id: UUID) -> Task | None:
        model = await self._session.get(TaskModel, task_id)
        return to_domain(model) if model else None

    async def list_for_workspace(
        self,
        workspace_id: UUID,
        *,
        project_id: UUID | None = None,
        include_completed: bool = False,
    ) -> list[Task]:
        statement = (
            sa.select(TaskModel)
            .join(ProjectModel, TaskModel.project_id == ProjectModel.id)
            .where(ProjectModel.workspace_id == workspace_id)
        )
        if project_id is not None:
            statement = statement.where(TaskModel.project_id == project_id)
        if not include_completed:
            statement = statement.where(TaskModel.completed_at.is_(None))
        statement = statement.order_by(sa.func.lower(TaskModel.name))
        models = (await self._session.execute(statement)).scalars().all()
        return [to_domain(model) for model in models]

    async def find_by_name(self, project_id: UUID, name: str) -> Task | None:
        statement = sa.select(TaskModel).where(
            TaskModel.project_id == project_id,
            sa.func.lower(TaskModel.name) == name.strip().lower(),
            TaskModel.completed_at.is_(None),
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return to_domain(model) if model else None

    async def add(self, task: Task) -> Task:
        model = TaskModel(**task.model_dump())
        self._session.add(model)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def update(self, task: Task) -> Task:
        model = await self._session.get(TaskModel, task.id)
        if model is None:
            raise TaskNotFound
        for field, value in task.model_dump().items():
            setattr(model, field, value)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def delete(self, task_id: UUID) -> None:
        model = await self._session.get(TaskModel, task_id)
        if model is None:
            raise TaskNotFound
        await self._session.delete(model)
        await self._session.flush()
