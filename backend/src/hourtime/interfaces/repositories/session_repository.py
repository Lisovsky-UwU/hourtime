from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from hourtime.domain.entities import Session


class SessionRepository(ABC):
    """Persistence for login sessions.

    Whether reads are served from a cache is an infrastructure concern — no
    use case may depend on it.
    """

    @abstractmethod
    async def get_by_access_token_hash(self, token_hash: str) -> Session | None: ...

    @abstractmethod
    async def get_by_refresh_token_hash(self, token_hash: str) -> Session | None: ...

    @abstractmethod
    async def add(self, session: Session) -> Session: ...

    @abstractmethod
    async def update(self, session: Session) -> Session: ...

    @abstractmethod
    async def revoke_all_for_user(
        self, user_id: UUID, at: datetime, *, keep: UUID | None = None
    ) -> int:
        """Revoke every live session of a user except `keep`; returns how many were affected."""

    @abstractmethod
    async def delete_expired_before(self, cutoff: datetime) -> int:
        """Drop sessions whose refresh token expired before `cutoff` (retention)."""
