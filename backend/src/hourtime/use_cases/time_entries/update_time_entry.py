from typing import Any

from hourtime.domain.entities import TimeEntry
from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import (
    ProjectRepository,
    TagRepository,
    TimeEntryRepository,
)
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.access import get_owned_time_entry
from hourtime.use_cases.dto import UpdateTimeEntryInput
from hourtime.use_cases.time_entries.rules import (
    END_TIME,
    START_TIME,
    reject_future,
    resolve_project,
    resolve_tags,
)


class UpdateTimeEntry:
    """Edits an entry from the list: project, tags, comment, billable, start and stop time.

    A running entry stays running unless a stop time is supplied — sending
    `project_id: null` detaches the project, omitting the field leaves it be.
    Likewise `tag_ids: []` removes every tag and an omitted `tag_ids` keeps them.
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

    async def execute(self, data: UpdateTimeEntryInput) -> TimeEntry:
        entry = await get_owned_time_entry(
            self._entries, data.user_id, data.workspace_id, data.entry_id
        )
        now = self._clock.now()
        changes: dict[str, Any] = {}

        if data.provided("project_id"):
            project = await resolve_project(self._projects, data.workspace_id, data.project_id)
            changes["project_id"] = project.id if project else None
            # Moving an entry to another project takes that project's billable
            # default, as picking a project does for a new entry. Detaching the
            # project leaves the flag as it was.
            if project is not None and project.id != entry.project_id:
                changes["billable"] = project.billable

        if data.provided("billable"):
            if data.billable is None:
                raise ValidationError("billable must be true or false")
            changes["billable"] = data.billable

        if data.provided("tag_ids"):
            if data.tag_ids is None:
                raise ValidationError("tag_ids must be a list; send [] to remove every tag")
            changes["tag_ids"] = await resolve_tags(self._tags, data.workspace_id, data.tag_ids)

        if data.provided("description"):
            changes["description"] = data.description or ""

        if data.provided("started_at"):
            if data.started_at is None:
                raise ValidationError("The start time is required")
            reject_future(data.started_at, now, START_TIME)
            changes["started_at"] = data.started_at

        if data.provided("stopped_at"):
            if data.stopped_at is not None:
                reject_future(data.stopped_at, now, END_TIME)
            changes["stopped_at"] = data.stopped_at

        if not changes:
            return entry

        started_at = changes.get("started_at", entry.started_at)
        stopped_at = changes.get("stopped_at", entry.stopped_at)
        if stopped_at is not None and stopped_at <= started_at:
            raise ValidationError("The end time must be later than the start time")

        # Reopening an entry would collide with whatever is running now.
        if stopped_at is None and not entry.is_running:
            running = await self._entries.get_running(data.user_id)
            if running is not None and running.id != entry.id:
                raise ValidationError("Another timer is already running")

        changes["updated_at"] = now
        updated = await self._entries.update(entry.evolve(**changes))
        await self._uow.commit()
        return updated
