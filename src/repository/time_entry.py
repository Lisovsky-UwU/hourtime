import uuid
from datetime import date

from sqlalchemy import and_, or_, select

from src.database.converter import DatabaseModelsConverter
from src.database.orm.project import ProjectORM
from src.database.orm.task import TaskORM
from src.database.orm.time_entry import TimeEntryORM
from src.dto.time_entry import CreateTimeEntryPayload, TimeEntryForUser, UpdateTimeEntryPayload
from src.exceptions.types import IncorrectRequestError, NotFoundError
from src.models.time_entery import TimeEntryModel
from src.repository.mixin import DatabaseRepositoryMixin
from src.use_case.time_entry import TimeEntryUseCase


class TimeEntryRepositoryDB(DatabaseRepositoryMixin, TimeEntryUseCase):

    async def _get_orm_by_id(
        self,
        time_entry_id: uuid.UUID,
        return_deleted: bool = False,
    ) -> TimeEntryORM:
        filter_ = TimeEntryORM.id == time_entry_id
        if not return_deleted:
            filter_ = and_(filter_, TimeEntryORM.deleted == False)  # noqa: E712

        query = select(TimeEntryORM).filter(filter_)

        result = await self.session.execute(query)
        entry_orm = result.scalar()
        if entry_orm is None:
            raise NotFoundError(
                60,
                "Time entry not found",
                "Time entry not found in database by id",
            )

        return entry_orm

    async def _check_workspace_project_and_task(
        self,
        workspace_id: int,
        project_id: int | None,
        task_id: uuid.UUID | None,
    ) -> None:
        query = None
        if project_id is None and task_id is None:
            return

        if project_id is not None and task_id is not None:
            query = select(
                select(1).select_from(TaskORM).filter_by(
                    id=task_id,
                    workspace_id=workspace_id,
                    project_id=project_id,
                    deleted=False,
                ).exists(),
            )

        elif project_id is not None and task_id is None:
            query = select(
                select(1).select_from(ProjectORM).filter_by(
                    id=project_id,
                    workspace_id=workspace_id,
                    deleted=False,
                ).exists(),
            )

        else:
        # it's like elif project_id is None and task_id is not None:
            query = select(
                select(1).select_from(TaskORM).filter_by(
                    id=task_id,
                    workspace_id=workspace_id,
                    deleted=False,
                ).exists(),
            )

        result = await self.session.execute(query)
        if not result.scalar():
            raise IncorrectRequestError(
                63,
                "Relationship error",
                "There is no relationships for the transferred workspace, project, and task.",
            )

    async def create_entry(self, payload: CreateTimeEntryPayload) -> TimeEntryModel:
        if payload.end_date is None:
            query = select(
                select(1).select_from(TimeEntryORM).filter_by(
                    user_id=payload.user_id,
                    workspace_id=payload.workspace_id,
                    end_date=None,
                    deleted=False,
                ).exists(),
            )
            result = await self.session.execute(query)
            if result.scalar():
                raise IncorrectRequestError(
                    61,
                    "There is a running time",
                    "The user already has a running time in the specified workspace",
                )

        await self._check_workspace_project_and_task(
            payload.workspace_id,
            payload.project_id,
            payload.task_id,
        )

        entry_orm = TimeEntryORM(
            user_id=payload.user_id,
            comment=payload.comment or None,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            task_id=payload.task_id,
            start_date=payload.start_date,
            start_time=payload.start_time,
            end_date=payload.end_date if payload.end_time is not None else None,
            end_time=payload.end_time if payload.end_date is not None else None,
        )
        self.session.add(entry_orm)
        await self.session.commit()
        await self.session.refresh(entry_orm)
        return DatabaseModelsConverter.time_entry_orm_to_model(entry_orm)

    async def get_by_id(self, entry_id: uuid.UUID, return_deleted: bool = False) -> TimeEntryModel:
        return DatabaseModelsConverter.time_entry_orm_to_model(
            await self._get_orm_by_id(entry_id, return_deleted),
        )

    async def get_for_user(
        self,
        user_id: int,
        workspace_id: int | None,
        range_date_start: date,
        range_date_end: date,
    ) -> list[TimeEntryForUser]:
        filter_ = and_(
            TimeEntryORM.user_id == user_id,
            or_(
                TimeEntryORM.start_date.between(range_date_start, range_date_end),
                TimeEntryORM.end_date.between(range_date_start, range_date_end),
            ),
            TimeEntryORM.deleted == False,  # noqa: E712
        )
        if workspace_id is not None:
            filter_ = and_(filter_, TimeEntryORM.workspace_id == workspace_id)

        query = select(TimeEntryORM).where(filter_).order_by(
            TimeEntryORM.start_date,
            TimeEntryORM.start_time,
        )
        result = await self.session.execute(query)
        entry_list: list[TimeEntryForUser] = []
        for row in result.scalars():
            entry_list.append(
                TimeEntryForUser(
                    id=row.id,
                    comment=row.comment,
                    workspace_id=row.workspace_id,
                    project_id=row.project_id,
                    task_id=row.task_id,
                    start_date=row.start_date,
                    start_time=row.start_time,
                    end_date=row.end_date,
                    end_time=row.end_time,
                ),
            )

        return entry_list

    async def update_entry(self, payload: UpdateTimeEntryPayload) -> TimeEntryModel:
        entry_orm = await self._get_orm_by_id(payload.time_entry_id)
        if entry_orm.task_id != payload.task_id or entry_orm.project_id != payload.project_id:
            await self._check_workspace_project_and_task(
                entry_orm.workspace_id,
                payload.project_id,
                payload.task_id,
            )

        entry_orm.comment = payload.comment or None
        entry_orm.project_id = payload.project_id
        entry_orm.task_id = payload.task_id
        if payload.start_date is not None:
            entry_orm.start_date = payload.start_date
        if payload.start_time is not None:
            entry_orm.start_time = payload.start_time
        entry_orm.end_date = payload.end_date if payload.end_time is not None else None
        entry_orm.end_time = payload.end_time if payload.end_date is not None else None
        await self.session.commit()
        await self.session.refresh(entry_orm)
        return DatabaseModelsConverter.time_entry_orm_to_model(entry_orm)


    async def delete_entry(self, time_entry_id: uuid.UUID) -> None:
        entry_orm = await self._get_orm_by_id(time_entry_id)
        entry_orm.deleted = True
        await self.session.commit()

