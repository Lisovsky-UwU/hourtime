from src.dto.time_entry import CreateTimeEntryPayload
from src.exceptions.defined import ORGANIZATION_ACCESS_ERROR
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

    def create_entry_by_user(self, payload: CreateTimeEntryPayload) -> TimeEntryModel:
        ...

