from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from hourtime.domain.entities import TimeEntry


class TimeEntryRepository(ABC):
    @abstractmethod
    async def get_by_id(self, entry_id: UUID) -> TimeEntry | None: ...

    @abstractmethod
    async def get_running(self, user_id: UUID) -> TimeEntry | None:
        """The entry without a stop time, if the user has one."""

    @abstractmethod
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
        """Newest first, ordered by `started_at` descending.

        There is deliberately no `count`: paging asks for one row more than it
        needs and infers "there is more" from that, which keeps the list to a
        single query.
        """

    @abstractmethod
    async def add(self, entry: TimeEntry) -> TimeEntry: ...

    @abstractmethod
    async def update(self, entry: TimeEntry) -> TimeEntry: ...

    @abstractmethod
    async def delete(self, entry_id: UUID) -> None: ...
