from uuid import UUID

from hourtime.interfaces.repositories import WorkspaceMemberRepository
from hourtime.use_cases.dto import MemberWorkspace


class ListWorkspaces:
    def __init__(self, members: WorkspaceMemberRepository) -> None:
        self._members = members

    async def execute(self, user_id: UUID) -> list[MemberWorkspace]:
        found = await self._members.list_for_user(user_id)
        return [MemberWorkspace(workspace=workspace, role=role) for workspace, role in found]
