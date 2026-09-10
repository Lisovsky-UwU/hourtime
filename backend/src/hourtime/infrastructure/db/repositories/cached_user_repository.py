"""Caching layer for user lookups.

Authenticating a request resolves a session *and* the user behind it. Caching
only the session would leave a `SELECT ... FROM users` on every single request,
so the owner of the token is cached the same way.
"""

import logging
from uuid import UUID

from pydantic import ValidationError as PydanticValidationError

from hourtime.domain.entities import User
from hourtime.infrastructure.cache.base import CacheClient
from hourtime.infrastructure.cache.invalidation import DeferredInvalidation
from hourtime.infrastructure.db.repositories.user_repository import SqlUserRepository
from hourtime.interfaces.repositories import UserRepository

logger = logging.getLogger(__name__)

USER_KEY_PREFIX = "user:"


def user_key(user_id: UUID) -> str:
    return f"{USER_KEY_PREFIX}{user_id}"


class CachedUserRepository(UserRepository):
    """Note the blast radius: a row edited straight in Postgres — flipping
    `is_active`, say — keeps being served from cache until the TTL runs out.
    Changes made through the app invalidate immediately.
    """

    def __init__(self, inner: SqlUserRepository, cache: CacheClient, *, ttl_seconds: int) -> None:
        self._inner = inner
        self._cache = cache
        self._ttl_seconds = ttl_seconds
        self.invalidation = DeferredInvalidation(cache)

    async def get_by_id(self, user_id: UUID) -> User | None:
        key = user_key(user_id)

        cached = await self._cache.get(key)
        if cached is not None:
            user = self._deserialise(cached)
            if user is not None:
                return user

        user = await self._inner.get_by_id(user_id)
        if user is not None:
            await self._cache.set(key, user.model_dump_json(), self._ttl_seconds)
        return user

    async def get_by_email(self, email: str) -> User | None:
        # Only login and registration look users up by email, and both are cold
        # paths — caching them would add a second key to keep in step for no gain.
        return await self._inner.get_by_email(email)

    async def add(self, user: User) -> User:
        return await self._inner.add(user)

    async def update(self, user: User) -> User:
        stored = await self._inner.update(user)
        await self.invalidation.invalidate(user_key(stored.id))
        return stored

    def _deserialise(self, raw: str) -> User | None:
        try:
            return User.model_validate_json(raw)
        except PydanticValidationError:
            # Shape changed under a running deploy — treat it as a miss.
            logger.warning("dropping unreadable cached user", exc_info=True)
            return None
