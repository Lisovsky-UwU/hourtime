"""Every cache key in the application is minted here.

Keys are shared state: the reader that builds one and the writer that drops it
have to agree exactly, and a typo in either place fails silently as a permanent
cache miss or, worse, as a stale entry nobody invalidates. Keeping the format in
one class means the two sides cannot drift apart, and it stays obvious what the
cache actually holds.
"""

from uuid import UUID

SEPARATOR = ":"


class CacheKey:
    """Namespaced keys, one factory method per cached object."""

    @staticmethod
    def _build(namespace: str, *parts: object) -> str:
        return SEPARATOR.join([namespace, *(str(part) for part in parts)])

    @classmethod
    def session_by_access_token(cls, token_hash: str) -> str:
        """A login session, addressed by the digest of its access token."""
        return cls._build("session:access", token_hash)

    @classmethod
    def user(cls, user_id: UUID) -> str:
        return cls._build("user", user_id)
