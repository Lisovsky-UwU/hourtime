from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from hourtime.domain.entities import TimeEntry
from hourtime.domain.errors import NotFound
from hourtime.infrastructure.db.models import TimeEntryModel
from hourtime.infrastructure.db.repositories.integrity import translating_integrity_errors
from hourtime.interfaces.repositories import TimeEntryRepository


def to_domain(model: TimeEntryModel) -> TimeEntry:
    return TimeEntry(
        id=model.id,
        user_id=model.user_id,
        project_id=model.project_id,
        description=model.description,
        started_at=model.started_at,
        stopped_at=model.stopped_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlTimeEntryRepository(TimeEntryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entry_id: UUID) -> TimeEntry | None:
        model = await self._session.get(TimeEntryModel, entry_id)
        return to_domain(model) if model else None

    async def get_running(self, user_id: UUID) -> TimeEntry | None:
        statement = sa.select(TimeEntryModel).where(
            TimeEntryModel.user_id == user_id, TimeEntryModel.stopped_at.is_(None)
        )
        model = (await self._session.execute(statement)).scalars().first()
        return to_domain(model) if model else None

    def _filters(
        self,
        user_id: UUID,
        started_from: datetime | None,
        started_to: datetime | None,
        project_id: UUID | None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [TimeEntryModel.user_id == user_id]
        if started_from is not None:
            conditions.append(TimeEntryModel.started_at >= started_from)
        if started_to is not None:
            conditions.append(TimeEntryModel.started_at <= started_to)
        if project_id is not None:
            conditions.append(TimeEntryModel.project_id == project_id)
        return conditions

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
        project_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TimeEntry]:
        statement = (
            sa.select(TimeEntryModel)
            .where(*self._filters(user_id, started_from, started_to, project_id))
            .order_by(TimeEntryModel.started_at.desc(), TimeEntryModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        models = (await self._session.execute(statement)).scalars().all()
        return [to_domain(model) for model in models]

    async def count_for_user(
        self,
        user_id: UUID,
        *,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
        project_id: UUID | None = None,
    ) -> int:
        statement = (
            sa.select(sa.func.count())
            .select_from(TimeEntryModel)
            .where(*self._filters(user_id, started_from, started_to, project_id))
        )
        return (await self._session.execute(statement)).scalar_one()

    async def add(self, entry: TimeEntry) -> TimeEntry:
        model = TimeEntryModel(**entry.model_dump())
        self._session.add(model)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def update(self, entry: TimeEntry) -> TimeEntry:
        model = await self._session.get(TimeEntryModel, entry.id)
        if model is None:
            raise NotFound("Time entry not found")
        for field, value in entry.model_dump().items():
            setattr(model, field, value)
        # Flushing right away matters when a timer is being swapped: the old
        # entry must be closed before the new one is inserted, or the partial
        # unique index rejects the pair.
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def delete(self, entry_id: UUID) -> None:
        model = await self._session.get(TimeEntryModel, entry_id)
        if model is None:
            raise NotFound("Time entry not found")
        await self._session.delete(model)
        await self._session.flush()
