from abc import ABC, abstractmethod
from uuid import UUID

from hourtime.domain.entities import Tag


class TagRepository(ABC):
    @abstractmethod
    async def get_by_id(self, tag_id: UUID) -> Tag | None: ...

    @abstractmethod
    async def get_many(self, tag_ids: list[UUID]) -> list[Tag]:
        """The tags that exist among `tag_ids`, in no particular order."""

    @abstractmethod
    async def list_for_workspace(self, workspace_id: UUID) -> list[Tag]: ...

    @abstractmethod
    async def find_by_name(self, workspace_id: UUID, name: str) -> Tag | None:
        """Look up by name, case-insensitively."""

    @abstractmethod
    async def add(self, tag: Tag) -> Tag: ...

    @abstractmethod
    async def update(self, tag: Tag) -> Tag: ...

    @abstractmethod
    async def delete(self, tag_id: UUID) -> None:
        """Remove the tag; the entries that carried it simply lose it."""
