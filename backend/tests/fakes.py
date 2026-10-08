"""In-memory doubles so the use cases can be tested without Postgres or Redis."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from hourtime.domain.entities import (
    Client,
    Project,
    Session,
    Tag,
    TimeEntry,
    TimeEntrySuggestion,
    User,
    Workspace,
)
from hourtime.domain.errors import (
    ClientNameTaken,
    NotFound,
    ProjectNameTaken,
    TagNameTaken,
    TimerAlreadyRunning,
)
from hourtime.interfaces.repositories import (
    ClientRepository,
    ProjectRepository,
    SessionRepository,
    TagRepository,
    TimeEntryRepository,
    UserRepository,
    WorkspaceRepository,
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


class InMemoryWorkspaceRepository(WorkspaceRepository):
    def __init__(self) -> None:
        self.items: dict[UUID, Workspace] = {}

    async def add(self, workspace: Workspace) -> Workspace:
        self.items[workspace.id] = workspace
        return workspace


class InMemoryClientRepository(ClientRepository):
    """Deleting a client does not detach it from projects: this fake knows no projects."""

    def __init__(self, clients: list[Client] | None = None) -> None:
        self.items: dict[UUID, Client] = {client.id: client for client in clients or []}

    async def get_by_id(self, client_id: UUID) -> Client | None:
        return self.items.get(client_id)

    async def list_for_workspace(
        self, workspace_id: UUID, *, include_archived: bool = False
    ) -> list[Client]:
        found = [item for item in self.items.values() if item.workspace_id == workspace_id]
        if not include_archived:
            found = [item for item in found if not item.is_archived]
        return sorted(found, key=lambda item: item.name.lower())

    async def find_by_name(self, workspace_id: UUID, name: str) -> Client | None:
        wanted = name.strip().lower()
        return next(
            (
                item
                for item in self.items.values()
                if item.workspace_id == workspace_id
                and item.name.lower() == wanted
                and not item.is_archived
            ),
            None,
        )

    async def add(self, client: Client) -> Client:
        if await self.find_by_name(client.workspace_id, client.name) is not None:
            raise ClientNameTaken
        self.items[client.id] = client
        return client

    async def update(self, client: Client) -> Client:
        if client.id not in self.items:
            raise NotFound("Client not found")
        self.items[client.id] = client
        return client

    async def delete(self, client_id: UUID) -> None:
        if self.items.pop(client_id, None) is None:
            raise NotFound("Client not found")


class InMemoryTagRepository(TagRepository):
    """Deleting a tag does not take it off entries: this fake knows no entries."""

    def __init__(self, tags: list[Tag] | None = None) -> None:
        self.items: dict[UUID, Tag] = {tag.id: tag for tag in tags or []}

    async def get_by_id(self, tag_id: UUID) -> Tag | None:
        return self.items.get(tag_id)

    async def get_many(self, tag_ids: list[UUID]) -> list[Tag]:
        return [self.items[tag_id] for tag_id in set(tag_ids) if tag_id in self.items]

    async def list_for_workspace(self, workspace_id: UUID) -> list[Tag]:
        found = [item for item in self.items.values() if item.workspace_id == workspace_id]
        return sorted(found, key=lambda item: item.name.lower())

    async def find_by_name(self, workspace_id: UUID, name: str) -> Tag | None:
        wanted = name.strip().lower()
        return next(
            (
                item
                for item in self.items.values()
                if item.workspace_id == workspace_id and item.name.lower() == wanted
            ),
            None,
        )

    async def add(self, tag: Tag) -> Tag:
        if await self.find_by_name(tag.workspace_id, tag.name) is not None:
            raise TagNameTaken
        self.items[tag.id] = tag
        return tag

    async def update(self, tag: Tag) -> Tag:
        if tag.id not in self.items:
            raise NotFound("Tag not found")
        self.items[tag.id] = tag
        return tag

    async def delete(self, tag_id: UUID) -> None:
        if self.items.pop(tag_id, None) is None:
            raise NotFound("Tag not found")


class InMemoryProjectRepository(ProjectRepository):
    def __init__(self, projects: list[Project] | None = None) -> None:
        self.items: dict[UUID, Project] = {project.id: project for project in projects or []}

    async def get_by_id(self, project_id: UUID) -> Project | None:
        return self.items.get(project_id)

    async def list_for_workspace(
        self, workspace_id: UUID, *, include_archived: bool = False
    ) -> list[Project]:
        found = [item for item in self.items.values() if item.workspace_id == workspace_id]
        if not include_archived:
            found = [item for item in found if not item.is_archived]
        return sorted(found, key=lambda item: item.name.lower())

    async def find_by_name(self, workspace_id: UUID, name: str) -> Project | None:
        wanted = name.strip().lower()
        return next(
            (
                item
                for item in self.items.values()
                if item.workspace_id == workspace_id
                and item.name.lower() == wanted
                and not item.is_archived
            ),
            None,
        )

    async def add(self, project: Project) -> Project:
        if await self.find_by_name(project.workspace_id, project.name) is not None:
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
    """Mirrors the partial unique index that keeps one timer running per user.

    The `client_id` filter looks projects up in `projects`, when one is given.
    """

    def __init__(
        self,
        entries: list[TimeEntry] | None = None,
        projects: InMemoryProjectRepository | None = None,
    ) -> None:
        self.items: dict[UUID, TimeEntry] = {entry.id: entry for entry in entries or []}
        self._projects = projects

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
        workspace_id: UUID,
        started_from: datetime | None,
        started_to: datetime | None,
        project_id: UUID | None,
        client_id: UUID | None = None,
        tag_ids: list[UUID] | None = None,
        without_project: bool = False,
    ) -> list[TimeEntry]:
        found = [
            entry
            for entry in self.items.values()
            if entry.user_id == user_id and entry.workspace_id == workspace_id
        ]
        if started_from is not None:
            found = [entry for entry in found if entry.started_at >= started_from]
        if started_to is not None:
            found = [entry for entry in found if entry.started_at <= started_to]
        if project_id is not None:
            found = [entry for entry in found if entry.project_id == project_id]
        if without_project:
            found = [entry for entry in found if entry.project_id is None]
        if client_id is not None:
            projects = self._projects.items if self._projects else {}
            client_projects = {
                project.id for project in projects.values() if project.client_id == client_id
            }
            found = [entry for entry in found if entry.project_id in client_projects]
        if tag_ids:
            wanted = set(tag_ids)
            found = [entry for entry in found if wanted & set(entry.tag_ids)]
        return sorted(found, key=lambda entry: entry.started_at, reverse=True)

    async def list_for_user(
        self,
        user_id: UUID,
        workspace_id: UUID,
        *,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
        project_id: UUID | None = None,
        client_id: UUID | None = None,
        tag_ids: list[UUID] | None = None,
        without_project: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TimeEntry]:
        found = self._matching(
            user_id,
            workspace_id,
            started_from,
            started_to,
            project_id,
            client_id,
            tag_ids,
            without_project,
        )
        return found[offset : offset + limit]

    async def suggest(
        self, user_id: UUID, workspace_id: UUID, *, query: str = "", limit: int = 10
    ) -> list[TimeEntrySuggestion]:
        """Archived projects are not filtered here: this fake knows no projects."""
        needle = query.casefold()
        found: dict[tuple[str, UUID | None], TimeEntrySuggestion] = {}
        for entry in self._matching(user_id, workspace_id, None, None, None):
            key = (entry.description, entry.project_id)
            if not entry.description or key in found or needle not in entry.description.casefold():
                continue
            found[key] = TimeEntrySuggestion(
                description=entry.description,
                project_id=entry.project_id,
                last_used_at=entry.started_at,
            )
        return list(found.values())[:limit]

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

    async def revoke_all_for_user(
        self, user_id: UUID, at: datetime, *, keep: UUID | None = None
    ) -> int:
        revoked = 0
        for key, item in list(self.items.items()):
            if item.user_id == user_id and not item.is_revoked and item.id != keep:
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
