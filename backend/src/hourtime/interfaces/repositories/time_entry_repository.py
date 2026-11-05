from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from hourtime.domain.entities import TimeEntry, TimeEntrySuggestion


class TimeEntryRepository(ABC):
    @abstractmethod
    async def get_by_id(self, entry_id: UUID) -> TimeEntry | None: ...

    @abstractmethod
    async def get_running(self, user_id: UUID) -> TimeEntry | None:
        """The entry without a stop time, if the user has one in any workspace."""

    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        workspace_id: UUID,
        *,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
        project_id: UUID | None = None,
        client_id: UUID | None = None,
        task_id: UUID | None = None,
        tag_ids: list[UUID] | None = None,
        without_project: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TimeEntry]:
        """Newest first, ordered by `started_at` descending.

        `client_id` keeps entries whose project belongs to that client,
        `task_id` keeps entries tracked against that task,
        `tag_ids` keeps entries carrying at least one of the tags, and
        `without_project` keeps entries with no project at all.

        There is deliberately no `count`: paging asks for one row more than it
        needs and infers "there is more" from that, which keeps the list to a
        single query.
        """

    @abstractmethod
    async def suggest(
        self, user_id: UUID, workspace_id: UUID, *, query: str = "", limit: int = 10
    ) -> list[TimeEntrySuggestion]:
        """Distinct (description, project, task) triples, most recently used first.

        Only triples with a description whose text contains `query`
        case-insensitively; triples pointing at an archived project are left out,
        since picking one would be rejected. Completed tasks are left out too:
        they cannot be assigned to a new entry.
        """

    @abstractmethod
    async def add(self, entry: TimeEntry) -> TimeEntry:
        """Store the entry together with its `tag_ids`."""

    @abstractmethod
    async def update(self, entry: TimeEntry) -> TimeEntry:
        """Store the entry; its tags become exactly `entry.tag_ids`."""

    @abstractmethod
    async def delete(self, entry_id: UUID) -> None: ...
