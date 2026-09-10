"""Caching layer for session lookups.

Every authenticated request resolves a bearer token, and going to Postgres for
each one is wasteful. The cache sits here, behind `SessionRepository`, so the
use cases stay unaware of it.
"""

import logging
from datetime import datetime
from uuid import UUID

from pydantic import ValidationError as PydanticValidationError

from hourtime.domain.entities import Session
from hourtime.infrastructure.cache.base import CacheClient
from hourtime.infrastructure.cache.invalidation import DeferredInvalidation
from hourtime.infrastructure.db.repositories.session_repository import SqlSessionRepository
from hourtime.interfaces.repositories import SessionRepository
from hourtime.interfaces.services import Clock

logger = logging.getLogger(__name__)

ACCESS_KEY_PREFIX = "session:access:"


def access_key(token_hash: str) -> str:
    return f"{ACCESS_KEY_PREFIX}{token_hash}"


class CachedSessionRepository(SessionRepository):
    def __init__(
        self,
        inner: SqlSessionRepository,
        cache: CacheClient,
        clock: Clock,
        *,
        ttl_seconds: int,
    ) -> None:
        self._inner = inner
        self._cache = cache
        self._clock = clock
        self._ttl_seconds = ttl_seconds
        self.invalidation = DeferredInvalidation(cache)

    # --- reads ---------------------------------------------------------------

    async def get_by_access_token_hash(self, token_hash: str) -> Session | None:
        key = access_key(token_hash)

        cached = await self._cache.get(key)
        if cached is not None:
            session = self._deserialise(cached)
            if session is not None:
                return session

        session = await self._inner.get_by_access_token_hash(token_hash)
        if session is not None:
            await self._store(key, session)
        # Misses are not cached: a flood of invented tokens would otherwise
        # evict the entries that matter.
        return session

    async def get_by_refresh_token_hash(self, token_hash: str) -> Session | None:
        # Refresh happens rarely and rotates tokens, so caching it would only
        # add ways to serve a stale session.
        return await self._inner.get_by_refresh_token_hash(token_hash)

    # --- writes --------------------------------------------------------------

    async def add(self, session: Session) -> Session:
        return await self._inner.add(session)

    async def update(self, session: Session) -> Session:
        stored = await self._inner.update(session)
        await self.invalidation.invalidate(access_key(stored.access_token_hash))
        return stored

    async def revoke_all_for_user(self, user_id: UUID, at: datetime) -> int:
        hashes = await self._inner.active_access_hashes(user_id)
        revoked = await self._inner.revoke_all_for_user(user_id, at)
        await self.invalidation.invalidate(*(access_key(digest) for digest in hashes))
        return revoked

    async def delete_expired_before(self, cutoff: datetime) -> int:
        # Cached copies of these are already past `access_expires_at`, so the
        # authentication use case rejects them regardless of the cache.
        return await self._inner.delete_expired_before(cutoff)

    # --- helpers -------------------------------------------------------------

    async def _store(self, key: str, session: Session) -> None:
        remaining = int((session.access_expires_at - self._clock.now()).total_seconds())
        # Never outlive the access token the entry describes.
        await self._cache.set(key, session.model_dump_json(), min(self._ttl_seconds, remaining))

    def _deserialise(self, raw: str) -> Session | None:
        try:
            return Session.model_validate_json(raw)
        except PydanticValidationError:
            # Shape changed under a running deploy — treat it as a miss.
            logger.warning("dropping unreadable cached session", exc_info=True)
            return None
