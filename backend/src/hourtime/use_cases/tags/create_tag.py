from uuid import uuid4

from hourtime.domain.entities import Tag
from hourtime.domain.errors import TagNameTaken
from hourtime.interfaces.repositories import TagRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.dto import CreateTagInput


class CreateTag:
    def __init__(self, tags: TagRepository, clock: Clock, uow: UnitOfWork) -> None:
        self._tags = tags
        self._clock = clock
        self._uow = uow

    async def execute(self, data: CreateTagInput) -> Tag:
        name = data.name.strip()
        if await self._tags.find_by_name(data.workspace_id, name) is not None:
            raise TagNameTaken

        now = self._clock.now()
        tag = Tag(
            id=uuid4(),
            workspace_id=data.workspace_id,
            name=name,
            created_at=now,
            updated_at=now,
        )
        stored = await self._tags.add(tag)
        await self._uow.commit()
        return stored
