from uuid import UUID

from hourtime.interfaces.repositories import SessionRepository
from hourtime.interfaces.services import Clock, TokenGenerator, UnitOfWork


class LogoutUser:
    """Revokes the current session, or every session of the user."""

    def __init__(
        self,
        sessions: SessionRepository,
        tokens: TokenGenerator,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._sessions = sessions
        self._tokens = tokens
        self._clock = clock
        self._uow = uow

    async def execute(self, access_token: str) -> None:
        session = await self._sessions.get_by_access_token_hash(self._tokens.hash(access_token))
        # Logging out an already-dead session is a no-op, not an error.
        if session is not None and not session.is_revoked:
            await self._sessions.update(session.revoke(self._clock.now()))
            await self._uow.commit()

    async def execute_all(self, user_id: UUID) -> int:
        revoked = await self._sessions.revoke_all_for_user(user_id, self._clock.now())
        await self._uow.commit()
        return revoked
