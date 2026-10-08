from uuid import UUID

from hourtime.domain.entities import Tag
from hourtime.interfaces.repositories import TagRepository


class ListTags:
    def __init__(self, tags: TagRepository) -> None:
        self._tags = tags

    async def execute(self, workspace_id: UUID) -> list[Tag]:
        return await self._tags.list_for_workspace(workspace_id)
