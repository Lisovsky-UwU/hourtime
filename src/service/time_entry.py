import uuid

from src.dto.time_entry import (
    CreateTimeEntryPayload,
    TimeEntryForUser,
    TimeEntryGetFilterData,
    UpdateTimeEntryPayload,
)
from src.exceptions.defined import ORGANIZATION_ACCESS_ERROR
from src.exceptions.types import NotFoundError
from src.models.time_entery import TimeEntryModel
from src.use_case.time_entry import TimeEntryUseCase
from src.use_case.workspace import WorkspaceUseCase


class TimeEntryService:

    def __init__(
        self,
        time_entry_repository: TimeEntryUseCase,
        workspace_repository: WorkspaceUseCase,
    ):
        self.time_entry_repository = time_entry_repository
        self.workspace_repository = workspace_repository

    async def _check_access_to_workspace(self, user_id: int, workspace_id: int) -> None:
        user_access = await self.workspace_repository.get_user_access(
            user_id,
            workspace_id,
        )
        if user_access is None:
            raise ORGANIZATION_ACCESS_ERROR

    async def create_entry_by_user(self, payload: CreateTimeEntryPayload) -> TimeEntryModel:
        await self._check_access_to_workspace(payload.user_id, payload.workspace_id)
        return await self.time_entry_repository.create_entry(payload)

    async def get_for_user(self, filter_data: TimeEntryGetFilterData) -> list[TimeEntryForUser]:
        return await self.time_entry_repository.get_for_user(
            filter_data.user_id,
            filter_data.workspace_id,
            filter_data.range_date_start,
            filter_data.range_date_end,
        )

    async def update_entry_by_user(
        self,
        user_id: int,
        payload: UpdateTimeEntryPayload,
    ) -> TimeEntryModel:
        time_entry = await self.time_entry_repository.get_by_id(payload.time_entry_id)
        if user_id != time_entry.user_id:
            raise NotFoundError(
                60,
                "Time entry not found",
                "Time entry not found in database by id",
            )

        return await self.time_entry_repository.update_entry(payload)

    async def delete_entry_by_user(self, user_id: int, time_entry_id: uuid.UUID) -> None:
        time_entry = await self.time_entry_repository.get_by_id(time_entry_id)
        if user_id != time_entry.user_id:
            raise NotFoundError(
                60,
                "Time entry not found",
                "Time entry not found in database by id",
            )

        return await self.time_entry_repository.delete_entry(time_entry_id)

