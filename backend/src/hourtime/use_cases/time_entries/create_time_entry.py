from uuid import uuid4

from hourtime.domain.entities import TimeEntry
from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import (
    ProjectRepository,
    TagRepository,
    TimeEntryRepository,
)
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.dto import CreateTimeEntryInput
from hourtime.use_cases.time_entries.rules import (
    END_TIME,
    START_TIME,
    reject_future,
    resolve_project,
    resolve_tags,
)


class CreateTimeEntry:
    """Adds a finished entry by hand, for work that was not tracked live."""

    def __init__(
        self,
        entries: TimeEntryRepository,
        projects: ProjectRepository,
        tags: TagRepository,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._entries = entries
        self._projects = projects
        self._tags = tags
        self._clock = clock
        self._uow = uow

    async def execute(self, data: CreateTimeEntryInput) -> TimeEntry:
        now = self._clock.now()
        reject_future(data.started_at, now, START_TIME)
        reject_future(data.stopped_at, now, END_TIME)
        if data.stopped_at <= data.started_at:
            raise ValidationError("The end time must be later than the start time")

        project_id = await resolve_project(self._projects, data.workspace_id, data.project_id)
        tag_ids = await resolve_tags(self._tags, data.workspace_id, data.tag_ids)

        entry = TimeEntry(
            id=uuid4(),
            user_id=data.user_id,
            workspace_id=data.workspace_id,
            project_id=project_id,
            tag_ids=tag_ids,
            description=data.description,
            started_at=data.started_at,
            stopped_at=data.stopped_at,
            created_at=now,
            updated_at=now,
        )
        stored = await self._entries.add(entry)
        await self._uow.commit()
        return stored
