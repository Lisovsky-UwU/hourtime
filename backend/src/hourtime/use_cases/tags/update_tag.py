from hourtime.domain.entities import Tag
from hourtime.domain.errors import TagNameTaken
from hourtime.interfaces.repositories import TagRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.access import get_workspace_tag
from hourtime.use_cases.dto import UpdateTagInput


class UpdateTag:
    """Renames a tag; there is nothing else about a tag to change."""

    def __init__(self, tags: TagRepository, clock: Clock, uow: UnitOfWork) -> None:
        self._tags = tags
        self._clock = clock
        self._uow = uow

    async def execute(self, data: UpdateTagInput) -> Tag:
        tag = await get_workspace_tag(self._tags, data.workspace_id, data.tag_id)
        name = data.name.strip()
        clash = await self._tags.find_by_name(data.workspace_id, name)
        if clash is not None and clash.id != tag.id:
            raise TagNameTaken

        updated = await self._tags.update(tag.evolve(name=name, updated_at=self._clock.now()))
        await self._uow.commit()
        return updated
