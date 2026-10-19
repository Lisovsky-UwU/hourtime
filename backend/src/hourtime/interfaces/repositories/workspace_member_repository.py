from abc import ABC, abstractmethod
from uuid import UUID

from hourtime.domain.entities import MemberRole, Workspace, WorkspaceMember


class WorkspaceMemberRepository(ABC):
    @abstractmethod
    async def get(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None: ...

    @abstractmethod
    async def list_for_user(self, user_id: UUID) -> list[tuple[Workspace, MemberRole]]:
        """Every workspace the user is in, with their role there, by name."""

    @abstractmethod
    async def add(self, member: WorkspaceMember) -> WorkspaceMember: ...
