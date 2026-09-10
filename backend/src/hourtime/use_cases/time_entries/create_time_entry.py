from uuid import uuid4

from hourtime.domain.entities import TimeEntry
from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import ProjectRepository, TimeEntryRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.dto import CreateTimeEntryInput
from hourtime.use_cases.time_entries.rules import (
    END_TIME,
    START_TIME,
    reject_future,
    resolve_project,
)


class CreateTimeEntry:
    """Adds a finished entry by hand, for work that was not tracked live."""

    def __init__(
        self,
        entries: TimeEntryRepository,
        projects: ProjectRepository,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._entries = entries
        self._projects = projects
        self._clock = clock
        self._uow = uow

    async def execute(self, data: CreateTimeEntryInput) -> TimeEntry:
        now = self._clock.now()
        reject_future(data.started_at, now, START_TIME)
        reject_future(data.stopped_at, now, END_TIME)
        if data.stopped_at <= data.started_at:
            raise ValidationError("The end time must be later than the start time")

        project_id = await resolve_project(self._projects, data.user_id, data.project_id)

        entry = TimeEntry(
            id=uuid4(),
            user_id=data.user_id,
            project_id=project_id,
            description=data.description,
            started_at=data.started_at,
            stopped_at=data.stopped_at,
            created_at=now,
            updated_at=now,
        )
        stored = await self._entries.add(entry)
        await self._uow.commit()
        return stored
