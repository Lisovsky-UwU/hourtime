from hourtime.domain.errors import AccountDisabled, InvalidToken, SessionExpired
from hourtime.interfaces.repositories import SessionRepository, UserRepository
from hourtime.interfaces.services import Clock, TokenGenerator
from hourtime.use_cases.dto import AuthenticatedUser


class AuthenticateAccessToken:
    """Resolves a bearer token into the user behind it.

    Runs on every authenticated request, so it only reads — `last_used_at` is
    refreshed during token rotation instead of writing on each call.
    """

    def __init__(
        self,
        sessions: SessionRepository,
        users: UserRepository,
        tokens: TokenGenerator,
        clock: Clock,
    ) -> None:
        self._sessions = sessions
        self._users = users
        self._tokens = tokens
        self._clock = clock

    async def execute(self, access_token: str) -> AuthenticatedUser:
        token = access_token.strip()
        if not token:
            raise InvalidToken

        session = await self._sessions.get_by_access_token_hash(self._tokens.hash(token))
        if session is None or session.is_revoked:
            raise InvalidToken

        if self._clock.now() >= session.access_expires_at:
            raise SessionExpired

        user = await self._users.get_by_id(session.user_id)
        if user is None:
            raise InvalidToken
        if not user.is_active:
            raise AccountDisabled

        return AuthenticatedUser(user=user, session_id=session.id)
