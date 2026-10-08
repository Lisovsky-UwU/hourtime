from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.domain.entities import Tag
from hourtime.domain.errors import NotFound
from hourtime.infrastructure.db.models import TagModel
from hourtime.infrastructure.db.repositories.integrity import translating_integrity_errors
from hourtime.interfaces.repositories import TagRepository


def to_domain(model: TagModel) -> Tag:
    return Tag(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlTagRepository(TagRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, tag_id: UUID) -> Tag | None:
        model = await self._session.get(TagModel, tag_id)
        return to_domain(model) if model else None

    async def get_many(self, tag_ids: list[UUID]) -> list[Tag]:
        if not tag_ids:
            return []
        statement = sa.select(TagModel).where(TagModel.id.in_(tag_ids))
        models = (await self._session.execute(statement)).scalars().all()
        return [to_domain(model) for model in models]

    async def list_for_workspace(self, workspace_id: UUID) -> list[Tag]:
        statement = (
            sa.select(TagModel)
            .where(TagModel.workspace_id == workspace_id)
            .order_by(sa.func.lower(TagModel.name))
        )
        models = (await self._session.execute(statement)).scalars().all()
        return [to_domain(model) for model in models]

    async def find_by_name(self, workspace_id: UUID, name: str) -> Tag | None:
        statement = sa.select(TagModel).where(
            TagModel.workspace_id == workspace_id,
            sa.func.lower(TagModel.name) == name.strip().lower(),
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return to_domain(model) if model else None

    async def add(self, tag: Tag) -> Tag:
        model = TagModel(**tag.model_dump())
        self._session.add(model)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def update(self, tag: Tag) -> Tag:
        model = await self._session.get(TagModel, tag.id)
        if model is None:
            raise NotFound("Tag not found")
        for field, value in tag.model_dump().items():
            setattr(model, field, value)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def delete(self, tag_id: UUID) -> None:
        model = await self._session.get(TagModel, tag_id)
        if model is None:
            raise NotFound("Tag not found")
        # `time_entry_tags` cascades, which takes the tag off every entry.
        await self._session.delete(model)
        await self._session.flush()
