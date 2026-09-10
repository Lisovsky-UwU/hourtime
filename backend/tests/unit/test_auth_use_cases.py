from datetime import timedelta

import pytest

from hourtime.domain.errors import (
    AccountDisabled,
    EmailAlreadyUsed,
    InvalidCredentials,
    InvalidToken,
    RegistrationDisabled,
    SessionExpired,
    ValidationError,
)
from hourtime.use_cases.auth import (
    AuthenticateAccessToken,
    LoginUser,
    LogoutUser,
    PurgeExpiredSessions,
    RefreshSession,
    RegisterUser,
    SessionIssuer,
)
from hourtime.use_cases.dto import (
    LoginUserInput,
    RefreshSessionInput,
    RegisterUserInput,
)
from tests.factories import make_user
from tests.fakes import (
    FakeClock,
    FakePasswordHasher,
    FakeTokenGenerator,
    FakeUnitOfWork,
    InMemorySessionRepository,
    InMemoryUserRepository,
)

ACCESS_TTL = timedelta(minutes=30)
REFRESH_TTL = timedelta(days=30)


class AuthWorld:
    """Everything the auth use cases need, wired to in-memory doubles."""

    def __init__(self, *, allow_registration: bool = True) -> None:
        self.clock = FakeClock()
        self.users = InMemoryUserRepository()
        self.sessions = InMemorySessionRepository()
        self.hasher = FakePasswordHasher()
        self.tokens = FakeTokenGenerator()
        self.uow = FakeUnitOfWork()
        self.issuer = SessionIssuer(
            self.sessions, self.tokens, self.clock, ACCESS_TTL, REFRESH_TTL
        )
        self.register = RegisterUser(
            self.users,
            self.hasher,
            self.clock,
            self.uow,
            allow_registration=allow_registration,
            password_min_length=10,
        )
        self.login = LoginUser(self.users, self.hasher, self.issuer, self.clock, self.uow)
        self.refresh = RefreshSession(
            self.sessions, self.users, self.tokens, self.issuer, self.clock, self.uow
        )
        self.logout = LogoutUser(self.sessions, self.tokens, self.clock, self.uow)
        self.authenticate = AuthenticateAccessToken(
            self.sessions, self.users, self.tokens, self.clock
        )

    async def signed_up(self, email: str = "owner@example.com", password: str = "correct-horse"):
        await self.register.execute(RegisterUserInput(email=email, password=password))
        return await self.login.execute(LoginUserInput(email=email, password=password))


@pytest.fixture
def world() -> AuthWorld:
    return AuthWorld()


class TestRegister:
    async def test_creates_user_with_hashed_password(self, world: AuthWorld) -> None:
        user = await world.register.execute(
            RegisterUserInput(email="Owner@Example.com", password="correct-horse")
        )
        assert user.email == "owner@example.com"
        assert user.password_hash == "hashed:correct-horse"
        assert world.uow.commits == 1

    async def test_rejects_duplicate_email(self, world: AuthWorld) -> None:
        await world.register.execute(
            RegisterUserInput(email="owner@example.com", password="correct-horse")
        )
        with pytest.raises(EmailAlreadyUsed):
            await world.register.execute(
                RegisterUserInput(email="OWNER@example.com", password="another-password")
            )

    async def test_rejects_short_password(self, world: AuthWorld) -> None:
        with pytest.raises(ValidationError):
            await world.register.execute(RegisterUserInput(email="a@example.com", password="short"))

    async def test_respects_the_registration_switch(self) -> None:
        closed = AuthWorld(allow_registration=False)
        with pytest.raises(RegistrationDisabled):
            await closed.register.execute(
                RegisterUserInput(email="owner@example.com", password="correct-horse")
            )


class TestLogin:
    async def test_issues_a_token_pair(self, world: AuthWorld) -> None:
        result = await world.signed_up()
        assert result.tokens.access_token != result.tokens.refresh_token
        assert result.tokens.access_expires_at == world.clock.now() + ACCESS_TTL
        assert result.tokens.refresh_expires_at == world.clock.now() + REFRESH_TTL

    async def test_stores_only_digests(self, world: AuthWorld) -> None:
        result = await world.signed_up()
        stored = next(iter(world.sessions.items.values()))
        assert stored.access_token_hash == f"digest:{result.tokens.access_token}"
        assert stored.access_token_hash != result.tokens.access_token
        assert stored.refresh_token_hash != result.tokens.refresh_token

    async def test_rejects_wrong_password(self, world: AuthWorld) -> None:
        await world.signed_up()
        with pytest.raises(InvalidCredentials):
            await world.login.execute(
                LoginUserInput(email="owner@example.com", password="wrong-password")
            )

    async def test_unknown_email_still_hashes(self, world: AuthWorld) -> None:
        """Otherwise response time tells an attacker which emails exist."""
        before = world.hasher.hash_calls
        with pytest.raises(InvalidCredentials):
            await world.login.execute(
                LoginUserInput(email="nobody@example.com", password="correct-horse")
            )
        assert world.hasher.hash_calls == before + 1

    async def test_rejects_disabled_account(self, world: AuthWorld) -> None:
        await world.signed_up()
        user = await world.users.get_by_email("owner@example.com")
        assert user is not None
        await world.users.update(user.evolve(is_active=False))
        with pytest.raises(AccountDisabled):
            await world.login.execute(
                LoginUserInput(email="owner@example.com", password="correct-horse")
            )


class TestAuthenticate:
    async def test_resolves_the_owner(self, world: AuthWorld) -> None:
        login = await world.signed_up()
        current = await world.authenticate.execute(login.tokens.access_token)
        assert current.user.id == login.user.id

    async def test_rejects_unknown_token(self, world: AuthWorld) -> None:
        with pytest.raises(InvalidToken):
            await world.authenticate.execute("made-up")

    async def test_rejects_expired_access_token(self, world: AuthWorld) -> None:
        login = await world.signed_up()
        world.clock.advance(ACCESS_TTL + timedelta(seconds=1))
        with pytest.raises(SessionExpired):
            await world.authenticate.execute(login.tokens.access_token)

    async def test_rejects_token_after_logout(self, world: AuthWorld) -> None:
        login = await world.signed_up()
        await world.logout.execute(login.tokens.access_token)
        with pytest.raises(InvalidToken):
            await world.authenticate.execute(login.tokens.access_token)

    async def test_logout_all_kills_every_device(self, world: AuthWorld) -> None:
        first = await world.signed_up()
        second = await world.login.execute(
            LoginUserInput(email="owner@example.com", password="correct-horse")
        )
        assert await world.logout.execute_all(first.user.id) == 2
        for token in (first.tokens.access_token, second.tokens.access_token):
            with pytest.raises(InvalidToken):
                await world.authenticate.execute(token)


class TestRefresh:
    async def test_rotates_both_tokens(self, world: AuthWorld) -> None:
        login = await world.signed_up()
        refreshed = await world.refresh.execute(
            RefreshSessionInput(refresh_token=login.tokens.refresh_token)
        )
        assert refreshed.tokens.access_token != login.tokens.access_token
        assert refreshed.tokens.refresh_token != login.tokens.refresh_token
        assert refreshed.user.id == login.user.id

    async def test_old_access_token_dies_with_the_rotation(self, world: AuthWorld) -> None:
        login = await world.signed_up()
        await world.refresh.execute(RefreshSessionInput(refresh_token=login.tokens.refresh_token))
        with pytest.raises(InvalidToken):
            await world.authenticate.execute(login.tokens.access_token)

    async def test_replayed_refresh_token_revokes_everything(self, world: AuthWorld) -> None:
        """A second use of a rotated token means it leaked — drop all sessions."""
        login = await world.signed_up()
        rotated = await world.refresh.execute(
            RefreshSessionInput(refresh_token=login.tokens.refresh_token)
        )

        with pytest.raises(InvalidToken):
            await world.refresh.execute(
                RefreshSessionInput(refresh_token=login.tokens.refresh_token)
            )

        with pytest.raises(InvalidToken):
            await world.authenticate.execute(rotated.tokens.access_token)

    async def test_rejects_expired_refresh_token(self, world: AuthWorld) -> None:
        login = await world.signed_up()
        world.clock.advance(REFRESH_TTL + timedelta(seconds=1))
        with pytest.raises(SessionExpired):
            await world.refresh.execute(
                RefreshSessionInput(refresh_token=login.tokens.refresh_token)
            )


class TestRetention:
    async def test_drops_only_sessions_past_the_window(self, world: AuthWorld) -> None:
        await world.signed_up()
        purge = PurgeExpiredSessions(
            world.sessions, world.clock, world.uow, retention=timedelta(days=90)
        )

        assert await purge.execute() == 0

        world.clock.advance(REFRESH_TTL + timedelta(days=91))
        assert await purge.execute() == 1
        assert world.sessions.items == {}


async def test_password_is_rehashed_when_parameters_age(world: AuthWorld) -> None:
    user = make_user(email="owner@example.com", password_hash="hashed:correct-horse")
    await world.users.add(user)
    world.hasher.mark_stale("hashed:correct-horse")

    result = await world.login.execute(
        LoginUserInput(email="owner@example.com", password="correct-horse")
    )

    stored = await world.users.get_by_id(result.user.id)
    assert stored is not None
    assert stored.updated_at == world.clock.now()
