import abc
import uuid
from datetime import date

from src.dto.time_entry import CreateTimeEntryPayload, TimeEntryForUser, UpdateTimeEntryPayload
from src.models.time_entery import TimeEntryModel


class TimeEntryUseCase(abc.ABC):

    @abc.abstractmethod
    async def create_entry(self, payload: CreateTimeEntryPayload) -> TimeEntryModel:
        ...

    @abc.abstractmethod
    async def get_by_id(self, entry_id: uuid.UUID, return_deleted: bool = False) -> TimeEntryModel:
        ...

    @abc.abstractmethod
    async def get_for_user(
        self,
        user_id: int,
        workspace_id: int | None,
        range_date_start: date,
        range_date_end: date,
    ) -> list[TimeEntryForUser]:
        ...

    @abc.abstractmethod
    async def update_entry(self, payload: UpdateTimeEntryPayload) -> TimeEntryModel:
        ...

    @abc.abstractmethod
    async def delete_entry(self, time_entry_id: uuid.UUID) -> None:
        ...

