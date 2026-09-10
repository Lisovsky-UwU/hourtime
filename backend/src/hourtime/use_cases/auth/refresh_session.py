from hourtime.domain.errors import AccountDisabled, InvalidToken, SessionExpired
from hourtime.interfaces.repositories import SessionRepository, UserRepository
from hourtime.interfaces.services import Clock, TokenGenerator, UnitOfWork
from hourtime.use_cases.auth.session_issuer import SessionIssuer
from hourtime.use_cases.dto import LoginResult, RefreshSessionInput


class RefreshSession:
    """Rotates a token pair.

    Both halves are replaced on every refresh and the old session is revoked,
    so a stolen refresh token stops working as soon as the real client uses it.
    """

    def __init__(
        self,
        sessions: SessionRepository,
        users: UserRepository,
        tokens: TokenGenerator,
        issuer: SessionIssuer,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._sessions = sessions
        self._users = users
        self._tokens = tokens
        self._issuer = issuer
        self._clock = clock
        self._uow = uow

    async def execute(self, data: RefreshSessionInput) -> LoginResult:
        token_hash = self._tokens.hash(data.refresh_token)
        session = await self._sessions.get_by_refresh_token_hash(token_hash)
        if session is None:
            raise InvalidToken

        now = self._clock.now()

        if session.is_revoked:
            # Someone replayed a rotated token: assume the pair leaked and cut
            # every session of that user loose.
            await self._sessions.revoke_all_for_user(session.user_id, now)
            await self._uow.commit()
            raise InvalidToken("This refresh token has already been used")

        if now >= session.refresh_expires_at:
            raise SessionExpired

        user = await self._users.get_by_id(session.user_id)
        if user is None:
            raise InvalidToken
        if not user.is_active:
            raise AccountDisabled

        await self._sessions.update(session.revoke(now).touch(now))
        issued = await self._issuer.issue(
            user.id, user_agent=data.user_agent or session.user_agent, ip=data.ip or session.ip
        )
        await self._uow.commit()
        return LoginResult(user=user, tokens=issued.tokens)
