from uuid import uuid4

from hourtime.domain.entities import TimeEntry
from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import (
    ProjectRepository,
    TagRepository,
    TimeEntryRepository,
)
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.dto import StartTimerInput
from hourtime.use_cases.time_entries.rules import (
    START_TIME,
    reject_future,
    resolve_billable,
    resolve_project,
    resolve_tags,
)


class StartTimer:
    """Starts tracking. Like Toggl, starting a timer stops the one already running.

    Only one entry per user may be open at a time; the database enforces that
    with a partial unique index, this use case makes the swap graceful.
    """

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

    async def execute(self, data: StartTimerInput) -> TimeEntry:
        now = self._clock.now()
        started_at = data.started_at or now
        reject_future(started_at, now, START_TIME)
        started_at = min(started_at, now)

        project = await resolve_project(self._projects, data.workspace_id, data.project_id)
        tag_ids = await resolve_tags(self._tags, data.workspace_id, data.tag_ids)

        running = await self._entries.get_running(data.user_id)
        if running is not None:
            # Close the previous entry where the new one begins, so the two
            # never overlap.
            stop_at = min(now, started_at)
            if stop_at <= running.started_at:
                raise ValidationError(
                    "The start time overlaps the entry already running — stop or edit it first"
                )
            await self._entries.update(running.stop(stop_at))

        entry = TimeEntry(
            id=uuid4(),
            user_id=data.user_id,
            workspace_id=data.workspace_id,
            project_id=project.id if project else None,
            tag_ids=tag_ids,
            description=data.description,
            billable=resolve_billable(data.billable, project),
            started_at=started_at,
            stopped_at=None,
            created_at=now,
            updated_at=now,
        )
        stored = await self._entries.add(entry)
        await self._uow.commit()
        return stored
