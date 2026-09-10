from datetime import timedelta
from uuid import UUID, uuid4

from hourtime.domain.entities import Session
from hourtime.interfaces.repositories import SessionRepository
from hourtime.interfaces.services import Clock, TokenGenerator
from hourtime.use_cases.dto import IssuedSession, SessionTokens


class SessionIssuer:
    """Mints a session together with its token pair.

    Shared by login and refresh so both produce identical session shapes.
    """

    def __init__(
        self,
        sessions: SessionRepository,
        tokens: TokenGenerator,
        clock: Clock,
        access_ttl: timedelta,
        refresh_ttl: timedelta,
    ) -> None:
        self._sessions = sessions
        self._tokens = tokens
        self._clock = clock
        self._access_ttl = access_ttl
        self._refresh_ttl = refresh_ttl

    async def issue(
        self,
        user_id: UUID,
        *,
        user_agent: str | None = None,
        ip: str | None = None,
    ) -> IssuedSession:
        now = self._clock.now()
        access_token = self._tokens.generate()
        refresh_token = self._tokens.generate()

        session = Session(
            id=uuid4(),
            user_id=user_id,
            access_token_hash=self._tokens.hash(access_token),
            refresh_token_hash=self._tokens.hash(refresh_token),
            access_expires_at=now + self._access_ttl,
            refresh_expires_at=now + self._refresh_ttl,
            created_at=now,
            last_used_at=now,
            user_agent=user_agent,
            ip=ip,
        )
        stored = await self._sessions.add(session)

        return IssuedSession(
            session=stored,
            tokens=SessionTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                access_expires_at=stored.access_expires_at,
                refresh_expires_at=stored.refresh_expires_at,
            ),
        )
