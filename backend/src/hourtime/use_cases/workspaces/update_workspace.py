from typing import Any

from hourtime.domain.entities import Workspace
from hourtime.domain.errors import NotFound, ValidationError
from hourtime.interfaces.repositories import WorkspaceRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.dto import UpdateWorkspaceInput


class UpdateWorkspace:
    """Billing settings of the workspace. `default_hourly_rate: null` removes the rate."""

    def __init__(self, workspaces: WorkspaceRepository, clock: Clock, uow: UnitOfWork) -> None:
        self._workspaces = workspaces
        self._clock = clock
        self._uow = uow

    async def execute(self, data: UpdateWorkspaceInput) -> Workspace:
        workspace = await self._workspaces.get_by_id(data.workspace_id)
        if workspace is None:
            raise NotFound("Workspace not found")

        changes: dict[str, Any] = {}
        if data.provided("default_hourly_rate"):
            changes["default_hourly_rate"] = data.default_hourly_rate
        if data.provided("currency"):
            if data.currency is None:
                raise ValidationError("The currency is required")
            changes["currency"] = data.currency

        if not changes:
            return workspace

        changes["updated_at"] = self._clock.now()
        updated = await self._workspaces.update(workspace.evolve(**changes))
        await self._uow.commit()
        return updated
