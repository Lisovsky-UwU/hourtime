from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from hourtime.domain.entities import WorkspaceInvite


class WorkspaceInviteRepository(ABC):
    @abstractmethod
    async def get_by_id(self, invite_id: UUID) -> WorkspaceInvite | None: ...

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> WorkspaceInvite | None: ...

    @abstractmethod
    async def list_open(self, workspace_id: UUID, now: datetime) -> list[WorkspaceInvite]:
        """Unused and unexpired, newest first."""

    @abstractmethod
    async def add(self, invite: WorkspaceInvite) -> WorkspaceInvite: ...

    @abstractmethod
    async def update(self, invite: WorkspaceInvite) -> WorkspaceInvite: ...

    @abstractmethod
    async def delete(self, invite_id: UUID) -> None: ...
