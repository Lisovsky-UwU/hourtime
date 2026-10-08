from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from hourtime.domain.entities import TimeEntry, TimeEntrySuggestion
from hourtime.domain.errors import NotFound
from hourtime.infrastructure.db.models import ProjectModel, TimeEntryModel, TimeEntryTagModel
from hourtime.infrastructure.db.repositories.integrity import translating_integrity_errors
from hourtime.interfaces.repositories import TimeEntryRepository


def to_domain(model: TimeEntryModel, tag_ids: list[UUID]) -> TimeEntry:
    return TimeEntry(
        id=model.id,
        user_id=model.user_id,
        workspace_id=model.workspace_id,
        project_id=model.project_id,
        tag_ids=tag_ids,
        description=model.description,
        started_at=model.started_at,
        stopped_at=model.stopped_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _escape_like(text: str) -> str:
    """Typed `%` and `_` are meant literally, not as wildcards."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class SqlTimeEntryRepository(TimeEntryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _tag_ids_of(self, entry_ids: list[UUID]) -> dict[UUID, list[UUID]]:
        """Tags of many entries in one query, so a page never costs a query per entry."""
        found: dict[UUID, list[UUID]] = {entry_id: [] for entry_id in entry_ids}
        if not entry_ids:
            return found
        statement = sa.select(TimeEntryTagModel.time_entry_id, TimeEntryTagModel.tag_id).where(
            TimeEntryTagModel.time_entry_id.in_(entry_ids)
        )
        for entry_id, tag_id in (await self._session.execute(statement)).all():
            found[entry_id].append(tag_id)
        return found

    async def _to_domain_many(self, models: list[TimeEntryModel]) -> list[TimeEntry]:
        tag_ids = await self._tag_ids_of([model.id for model in models])
        return [to_domain(model, tag_ids[model.id]) for model in models]

    async def _to_domain_one(self, model: TimeEntryModel | None) -> TimeEntry | None:
        if model is None:
            return None
        return (await self._to_domain_many([model]))[0]

    async def _replace_tags(self, entry_id: UUID, tag_ids: list[UUID]) -> None:
        await self._session.execute(
            sa.delete(TimeEntryTagModel).where(TimeEntryTagModel.time_entry_id == entry_id)
        )
        if tag_ids:
            await self._session.execute(
                sa.insert(TimeEntryTagModel),
                [{"time_entry_id": entry_id, "tag_id": tag_id} for tag_id in tag_ids],
            )

    async def get_by_id(self, entry_id: UUID) -> TimeEntry | None:
        return await self._to_domain_one(await self._session.get(TimeEntryModel, entry_id))

    async def get_running(self, user_id: UUID) -> TimeEntry | None:
        statement = sa.select(TimeEntryModel).where(
            TimeEntryModel.user_id == user_id, TimeEntryModel.stopped_at.is_(None)
        )
        return await self._to_domain_one((await self._session.execute(statement)).scalars().first())

    def _filters(
        self,
        user_id: UUID,
        workspace_id: UUID,
        started_from: datetime | None,
        started_to: datetime | None,
        project_id: UUID | None,
        client_id: UUID | None,
        tag_ids: list[UUID] | None,
        without_project: bool,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [
            TimeEntryModel.user_id == user_id,
            TimeEntryModel.workspace_id == workspace_id,
        ]
        if started_from is not None:
            conditions.append(TimeEntryModel.started_at >= started_from)
        if started_to is not None:
            conditions.append(TimeEntryModel.started_at <= started_to)
        if project_id is not None:
            conditions.append(TimeEntryModel.project_id == project_id)
        if without_project:
            conditions.append(TimeEntryModel.project_id.is_(None))
        # EXISTS rather than JOIN: an entry with two matching tags must still
        # come back once, and paging must count entries, not joined rows.
        if client_id is not None:
            conditions.append(
                sa.exists().where(
                    ProjectModel.id == TimeEntryModel.project_id,
                    ProjectModel.client_id == client_id,
                )
            )
        if tag_ids:
            conditions.append(
                sa.exists().where(
                    TimeEntryTagModel.time_entry_id == TimeEntryModel.id,
                    TimeEntryTagModel.tag_id.in_(tag_ids),
                )
            )
        return conditions

    async def list_for_user(
        self,
        user_id: UUID,
        workspace_id: UUID,
        *,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
        project_id: UUID | None = None,
        client_id: UUID | None = None,
        tag_ids: list[UUID] | None = None,
        without_project: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TimeEntry]:
        filters = self._filters(
            user_id,
            workspace_id,
            started_from,
            started_to,
            project_id,
            client_id,
            tag_ids,
            without_project,
        )
        statement = (
            sa.select(TimeEntryModel)
            .where(*filters)
            .order_by(TimeEntryModel.started_at.desc(), TimeEntryModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        models = (await self._session.execute(statement)).scalars().all()
        return await self._to_domain_many(list(models))

    async def suggest(
        self, user_id: UUID, workspace_id: UUID, *, query: str = "", limit: int = 10
    ) -> list[TimeEntrySuggestion]:
        last_used = sa.func.max(TimeEntryModel.started_at).label("last_used_at")
        statement = (
            sa.select(TimeEntryModel.description, TimeEntryModel.project_id, last_used)
            .outerjoin(ProjectModel, ProjectModel.id == TimeEntryModel.project_id)
            .where(
                TimeEntryModel.user_id == user_id,
                TimeEntryModel.workspace_id == workspace_id,
                TimeEntryModel.description != "",
                ProjectModel.archived_at.is_(None),
            )
            .group_by(TimeEntryModel.description, TimeEntryModel.project_id)
            .order_by(last_used.desc())
            .limit(limit)
        )
        if query:
            statement = statement.where(
                TimeEntryModel.description.ilike(f"%{_escape_like(query)}%", escape="\\")
            )
        rows = (await self._session.execute(statement)).all()
        return [
            TimeEntrySuggestion(
                description=row.description,
                project_id=row.project_id,
                last_used_at=row.last_used_at,
            )
            for row in rows
        ]

    async def add(self, entry: TimeEntry) -> TimeEntry:
        model = TimeEntryModel(**entry.model_dump(exclude={"tag_ids"}))
        self._session.add(model)
        await translating_integrity_errors(self._session.flush)
        await self._replace_tags(model.id, entry.tag_ids)
        return to_domain(model, entry.tag_ids)

    async def update(self, entry: TimeEntry) -> TimeEntry:
        model = await self._session.get(TimeEntryModel, entry.id)
        if model is None:
            raise NotFound("Time entry not found")
        for field, value in entry.model_dump(exclude={"tag_ids"}).items():
            setattr(model, field, value)
        # Flushing right away matters when a timer is being swapped: the old
        # entry must be closed before the new one is inserted, or the partial
        # unique index rejects the pair.
        await translating_integrity_errors(self._session.flush)
        # Most updates, such as stopping a timer, keep the tags; skip the rewrite then.
        stored = (await self._tag_ids_of([entry.id]))[entry.id]
        if sorted(stored) != entry.tag_ids:
            await self._replace_tags(entry.id, entry.tag_ids)
        return to_domain(model, entry.tag_ids)

    async def delete(self, entry_id: UUID) -> None:
        model = await self._session.get(TimeEntryModel, entry_id)
        if model is None:
            raise NotFound("Time entry not found")
        await self._session.delete(model)
        await self._session.flush()
