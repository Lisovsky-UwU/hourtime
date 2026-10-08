from uuid import UUID

from hourtime.interfaces.repositories import TagRepository
from hourtime.interfaces.services import UnitOfWork
from hourtime.use_cases.access import get_workspace_tag


class DeleteTag:
    """Removes a tag; the entries that carried it keep everything else."""

    def __init__(self, tags: TagRepository, uow: UnitOfWork) -> None:
        self._tags = tags
        self._uow = uow

    async def execute(self, workspace_id: UUID, tag_id: UUID) -> None:
        tag = await get_workspace_tag(self._tags, workspace_id, tag_id)
        await self._tags.delete(tag.id)
        await self._uow.commit()
