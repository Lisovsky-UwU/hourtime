import abc

from src.dto.time_entry import CreateTimeEntryPayload, UpdateTimeEntryPayload
from src.models.time_entery import TimeEntryModel


class TimeEntryUseCase(abc.ABC):

    @abc.abstractmethod
    async def create_entry(self, payload: CreateTimeEntryPayload) -> TimeEntryModel:
        ...

    @abc.abstractmethod
    async def update_entry(self, payload: UpdateTimeEntryPayload) -> TimeEntryModel:
        ...

