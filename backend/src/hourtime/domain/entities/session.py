from datetime import datetime
from uuid import UUID

from hourtime.domain.entities.base import Entity, UtcDatetime


class Session(Entity):
    """A logged-in device.

    The raw tokens are handed to the client once and never stored; only their
    SHA-256 digests live here, so a database dump cannot be replayed as a login.
    """

    id: UUID
    user_id: UUID
    access_token_hash: str
    refresh_token_hash: str
    access_expires_at: UtcDatetime
    refresh_expires_at: UtcDatetime
    revoked_at: UtcDatetime | None = None
    created_at: UtcDatetime
    last_used_at: UtcDatetime
    user_agent: str | None = None
    ip: str | None = None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_access_usable(self, now: datetime) -> bool:
        return not self.is_revoked and now < self.access_expires_at

    def is_refresh_usable(self, now: datetime) -> bool:
        return not self.is_revoked and now < self.refresh_expires_at

    def revoke(self, at: datetime) -> "Session":
        return self.evolve(revoked_at=at)

    def touch(self, at: datetime) -> "Session":
        return self.evolve(last_used_at=at)
