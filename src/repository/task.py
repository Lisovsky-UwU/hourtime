import uuid
from operator import and_

from loguru import logger
from sqlalchemy import func, select

from src.database.converter import DatabaseModelsConverter
from src.database.orm.project import ProjectORM
from src.database.orm.task import TaskORM
from src.dto.task import CreateTaskPayload, TaskInWorkspace, UpdateTaskPayload
from src.exceptions.types import IncorrectRequestError, NotFoundError
from src.models.task import TaskModel
from src.repository.mixin import DatabaseRepositoryMixin
from src.use_case.task import TaskUseCase


class TaskRepositoryDB(DatabaseRepositoryMixin, TaskUseCase):

    async def _get_orm_by_id(self, task_id: uuid.UUID, return_deleted: bool = False) -> TaskORM:
        filter_ = TaskORM.id == task_id
        if not return_deleted:
            filter_ = and_(filter_, TaskORM.deleted == False)  # noqa: E712

        query = select(TaskORM).filter(filter_)

        result = await self.session.execute(query)
        user_orm = result.scalar()
        if user_orm is None:
            raise NotFoundError(
                50,
                "Task not found",
                "Task not found in database by id",
            )

        return user_orm

    async def _get_task_next_number(self, workspace_id: int) -> int:
        query = select(func.max(TaskORM.number)).filter_by(workspace_id=workspace_id)
        logger.debug(query)
        result = await self.session.execute(query)
        return (result.scalar() or 0) + 1

    async def create_task(self, payload: CreateTaskPayload) -> TaskModel:
        if payload.project_id is not None:
            query = select(ProjectORM.workspace_id).filter_by(id=payload.project_id, deleted=False)
            result = await self.session.execute(query)
            if result.scalar() != payload.workspace_id:
                raise IncorrectRequestError(
                    51,
                    "Incorrect project id",
                    "Specified project is not part of the workspace",
                )

        next_number = await self._get_task_next_number(payload.workspace_id)
        task_orm = TaskORM(
            number=next_number,
            name=payload.name,
            description=payload.description,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
        )
        self.session.add(task_orm)
        await self.session.commit()
        await self.session.refresh(task_orm)
        return DatabaseModelsConverter.task_orm_to_model(task_orm)

    async def get_by_id(self, task_id: uuid.UUID, return_deleted: bool = False) -> TaskModel:
        return DatabaseModelsConverter.task_orm_to_model(
            await self._get_orm_by_id(task_id, return_deleted),
        )

    async def get_by_workspace(self, workspace_id: int) -> list[TaskInWorkspace]:
        query = select(TaskORM).filter_by(workspace_id=workspace_id, deleted=False)
        result = await self.session.execute(query)
        task_list: list[TaskInWorkspace] = []
        for row in result.scalars():
            task_list.append(
                TaskInWorkspace(
                    id=row.id,
                    number=row.number,
                    name=row.name,
                    description=row.description,
                    project_id=row.project_id,
                ),
            )

        return task_list

    async def update_task(self, payload: UpdateTaskPayload) -> TaskModel:
        task_orm = await self._get_orm_by_id(payload.id)
        task_orm.name = payload.name
        task_orm.description = payload.description or None
        await self.session.commit()
        await self.session.refresh(task_orm)
        return DatabaseModelsConverter.task_orm_to_model(task_orm)

    async def delete_task(self, task_id: uuid.UUID) -> None:
        task_orm = await self._get_orm_by_id(task_id)
        task_orm.deleted = True
        await self.session.commit()

