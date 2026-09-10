"""In-memory doubles so the use cases can be tested without Postgres or Redis."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from hourtime.domain.entities import Project, Session, TimeEntry, User
from hourtime.domain.errors import NotFound, ProjectNameTaken, TimerAlreadyRunning
from hourtime.interfaces.repositories import (
    ProjectRepository,
    SessionRepository,
    TimeEntryRepository,
    UserRepository,
)
from hourtime.interfaces.services import Clock, PasswordHasher, TokenGenerator, UnitOfWork


class FakeClock(Clock):
    def __init__(self, start: datetime | None = None) -> None:
        self._now = start or datetime(2026, 3, 1, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> datetime:
        self._now += delta
        return self._now

    def set(self, moment: datetime) -> None:
        self._now = moment


class FakeUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def flush(self) -> None:
        pass


class FakePasswordHasher(PasswordHasher):
    """Reversible on purpose — these tests are about the flow, not about Argon2."""

    def __init__(self) -> None:
        self._stale: set[str] = set()
        self.hash_calls = 0

    def mark_stale(self, password_hash: str) -> None:
        """Pretend this hash was made with outdated parameters."""
        self._stale.add(password_hash)

    def hash(self, password: str) -> str:
        self.hash_calls += 1
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"

    def needs_rehash(self, password_hash: str) -> bool:
        return password_hash in self._stale


class FakeTokenGenerator(TokenGenerator):
    def __init__(self) -> None:
        self._counter = 0

    def generate(self) -> str:
        self._counter += 1
        return f"token-{self._counter}"

    def hash(self, token: str) -> str:
        return f"digest:{token}"


class InMemoryUserRepository(UserRepository):
    def __init__(self, users: list[User] | None = None) -> None:
        self.items: dict[UUID, User] = {user.id: user for user in users or []}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.items.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        wanted = email.strip().lower()
        return next((user for user in self.items.values() if user.email == wanted), None)

    async def add(self, user: User) -> User:
        self.items[user.id] = user
        return user

    async def update(self, user: User) -> User:
        if user.id not in self.items:
            raise NotFound("User not found")
        self.items[user.id] = user
        return user


class InMemoryProjectRepository(ProjectRepository):
    def __init__(self, projects: list[Project] | None = None) -> None:
        self.items: dict[UUID, Project] = {project.id: project for project in projects or []}

    async def get_by_id(self, project_id: UUID) -> Project | None:
        return self.items.get(project_id)

    async def list_for_user(
        self, user_id: UUID, *, include_archived: bool = False
    ) -> list[Project]:
        found = [item for item in self.items.values() if item.user_id == user_id]
        if not include_archived:
            found = [item for item in found if not item.is_archived]
        return sorted(found, key=lambda item: item.name.lower())

    async def find_by_name(self, user_id: UUID, name: str) -> Project | None:
        wanted = name.strip().lower()
        return next(
            (
                item
                for item in self.items.values()
                if item.user_id == user_id
                and item.name.lower() == wanted
                and not item.is_archived
            ),
            None,
        )

    async def add(self, project: Project) -> Project:
        if await self.find_by_name(project.user_id, project.name) is not None:
            raise ProjectNameTaken
        self.items[project.id] = project
        return project

    async def update(self, project: Project) -> Project:
        if project.id not in self.items:
            raise NotFound("Project not found")
        self.items[project.id] = project
        return project

    async def delete(self, project_id: UUID) -> None:
        if self.items.pop(project_id, None) is None:
            raise NotFound("Project not found")


class InMemoryTimeEntryRepository(TimeEntryRepository):
    """Mirrors the partial unique index that keeps one timer running per user."""

    def __init__(self, entries: list[TimeEntry] | None = None) -> None:
        self.items: dict[UUID, TimeEntry] = {entry.id: entry for entry in entries or []}

    def _check_single_running(self, entry: TimeEntry) -> None:
        if not entry.is_running:
            return
        clash = next(
            (
                other
                for other in self.items.values()
                if other.user_id == entry.user_id and other.is_running and other.id != entry.id
            ),
            None,
        )
        if clash is not None:
            raise TimerAlreadyRunning

    async def get_by_id(self, entry_id: UUID) -> TimeEntry | None:
        return self.items.get(entry_id)

    async def get_running(self, user_id: UUID) -> TimeEntry | None:
        return next(
            (
                entry
                for entry in self.items.values()
                if entry.user_id == user_id and entry.is_running
            ),
            None,
        )

    def _matching(
        self,
        user_id: UUID,
        started_from: datetime | None,
        started_to: datetime | None,
        project_id: UUID | None,
    ) -> list[TimeEntry]:
        found = [entry for entry in self.items.values() if entry.user_id == user_id]
        if started_from is not None:
            found = [entry for entry in found if entry.started_at >= started_from]
        if started_to is not None:
            found = [entry for entry in found if entry.started_at <= started_to]
        if project_id is not None:
            found = [entry for entry in found if entry.project_id == project_id]
        return sorted(found, key=lambda entry: entry.started_at, reverse=True)

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
        project_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TimeEntry]:
        found = self._matching(user_id, started_from, started_to, project_id)
        return found[offset : offset + limit]

    async def add(self, entry: TimeEntry) -> TimeEntry:
        self._check_single_running(entry)
        self.items[entry.id] = entry
        return entry

    async def update(self, entry: TimeEntry) -> TimeEntry:
        if entry.id not in self.items:
            raise NotFound("Time entry not found")
        self._check_single_running(entry)
        self.items[entry.id] = entry
        return entry

    async def delete(self, entry_id: UUID) -> None:
        if self.items.pop(entry_id, None) is None:
            raise NotFound("Time entry not found")


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self.items: dict[UUID, Session] = {}

    async def get_by_access_token_hash(self, token_hash: str) -> Session | None:
        return next(
            (item for item in self.items.values() if item.access_token_hash == token_hash), None
        )

    async def get_by_refresh_token_hash(self, token_hash: str) -> Session | None:
        return next(
            (item for item in self.items.values() if item.refresh_token_hash == token_hash), None
        )

    async def add(self, session: Session) -> Session:
        self.items[session.id] = session
        return session

    async def update(self, session: Session) -> Session:
        if session.id not in self.items:
            raise NotFound("Session not found")
        self.items[session.id] = session
        return session

    async def revoke_all_for_user(self, user_id: UUID, at: datetime) -> int:
        revoked = 0
        for key, item in list(self.items.items()):
            if item.user_id == user_id and not item.is_revoked:
                self.items[key] = item.revoke(at)
                revoked += 1
        return revoked

    async def delete_expired_before(self, cutoff: datetime) -> int:
        doomed = [
            key for key, item in self.items.items() if item.refresh_expires_at < cutoff
        ]
        for key in doomed:
            del self.items[key]
        return len(doomed)
