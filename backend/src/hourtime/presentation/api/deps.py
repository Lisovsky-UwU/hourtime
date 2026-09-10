"""Composition root.

This is the only module that knows which concrete adapter backs each interface.
Everything above it asks for a use case and gets one fully wired.
"""

from collections.abc import AsyncIterator
from contextlib import suppress
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hourtime.config import Settings
from hourtime.domain.errors import InvalidToken
from hourtime.infrastructure.cache import CacheClient
from hourtime.infrastructure.clock import SystemClock
from hourtime.infrastructure.db.cache_aware_unit_of_work import CacheAwareUnitOfWork
from hourtime.infrastructure.db.repositories.cached_session_repository import (
    CachedSessionRepository,
)
from hourtime.infrastructure.db.repositories.cached_user_repository import CachedUserRepository
from hourtime.infrastructure.db.repositories.project_repository import SqlProjectRepository
from hourtime.infrastructure.db.repositories.session_repository import SqlSessionRepository
from hourtime.infrastructure.db.repositories.time_entry_repository import SqlTimeEntryRepository
from hourtime.infrastructure.db.repositories.user_repository import SqlUserRepository
from hourtime.infrastructure.security.token_generator import OpaqueTokenGenerator
from hourtime.interfaces.repositories import (
    ProjectRepository,
    TimeEntryRepository,
)
from hourtime.interfaces.services import Clock, PasswordHasher, TokenGenerator, UnitOfWork
from hourtime.use_cases.auth import (
    AuthenticateAccessToken,
    LoginUser,
    LogoutUser,
    PurgeExpiredSessions,
    RefreshSession,
    RegisterUser,
    SessionIssuer,
)
from hourtime.use_cases.dto import AuthenticatedUser
from hourtime.use_cases.projects import CreateProject, DeleteProject, ListProjects, UpdateProject
from hourtime.use_cases.time_entries import (
    CreateTimeEntry,
    DeleteTimeEntry,
    GetRunningTimer,
    ListTimeEntries,
    StartTimer,
    StopTimer,
    UpdateTimeEntry,
)

# --- process-wide singletons -------------------------------------------------


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_cache(request: Request) -> CacheClient:
    cache: CacheClient = request.app.state.cache
    return cache


CacheDep = Annotated[CacheClient, Depends(get_cache)]


def get_password_hasher(request: Request) -> PasswordHasher:
    # Reused because building an Argon2 hasher per request is pure overhead.
    hasher: PasswordHasher = request.app.state.password_hasher
    return hasher


HasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]


def get_clock() -> Clock:
    return SystemClock()


ClockDep = Annotated[Clock, Depends(get_clock)]


def get_token_generator() -> TokenGenerator:
    return OpaqueTokenGenerator()


TokensDep = Annotated[TokenGenerator, Depends(get_token_generator)]


# --- per-request database session --------------------------------------------


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.sessionmaker
    async with factory() as session:
        try:
            yield session
        except Exception:
            # A failed flush leaves the transaction unusable; drop it so the
            # connection returns to the pool clean. If the connection itself
            # died, the rollback fails too — swallow that so the original error
            # is what the client hears about.
            with suppress(Exception):
                await session.rollback()
            raise


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


# --- repositories ------------------------------------------------------------


def get_user_repository(
    session: DbSessionDep, cache: CacheDep, settings: SettingsDep
) -> CachedUserRepository:
    return CachedUserRepository(
        SqlUserRepository(session), cache, ttl_seconds=settings.cache_ttl_seconds
    )


UsersDep = Annotated[CachedUserRepository, Depends(get_user_repository)]


def get_project_repository(session: DbSessionDep) -> ProjectRepository:
    return SqlProjectRepository(session)


ProjectsDep = Annotated[ProjectRepository, Depends(get_project_repository)]


def get_time_entry_repository(session: DbSessionDep) -> TimeEntryRepository:
    return SqlTimeEntryRepository(session)


EntriesDep = Annotated[TimeEntryRepository, Depends(get_time_entry_repository)]


def get_session_repository(
    session: DbSessionDep,
    cache: CacheDep,
    clock: ClockDep,
    settings: SettingsDep,
) -> CachedSessionRepository:
    return CachedSessionRepository(
        SqlSessionRepository(session),
        cache,
        clock,
        ttl_seconds=settings.cache_ttl_seconds,
    )


SessionsDep = Annotated[CachedSessionRepository, Depends(get_session_repository)]


def get_unit_of_work(
    session: DbSessionDep, sessions: SessionsDep, users: UsersDep
) -> UnitOfWork:
    # FastAPI caches dependencies per request, so these are the very repository
    # instances the use cases got — their pending invalidations are the ones flushed.
    return CacheAwareUnitOfWork(session, sessions.invalidation, users.invalidation)


UowDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]


# --- auth use cases ----------------------------------------------------------


def get_session_issuer(
    sessions: SessionsDep, tokens: TokensDep, clock: ClockDep, settings: SettingsDep
) -> SessionIssuer:
    return SessionIssuer(
        sessions,
        tokens,
        clock,
        access_ttl=timedelta(minutes=settings.access_token_ttl_minutes),
        refresh_ttl=timedelta(days=settings.refresh_token_ttl_days),
    )


IssuerDep = Annotated[SessionIssuer, Depends(get_session_issuer)]


def get_register_user(
    users: UsersDep, hasher: HasherDep, clock: ClockDep, uow: UowDep, settings: SettingsDep
) -> RegisterUser:
    return RegisterUser(
        users,
        hasher,
        clock,
        uow,
        allow_registration=settings.allow_registration,
        password_min_length=settings.password_min_length,
    )


def get_login_user(
    users: UsersDep, hasher: HasherDep, issuer: IssuerDep, clock: ClockDep, uow: UowDep
) -> LoginUser:
    return LoginUser(users, hasher, issuer, clock, uow)


def get_refresh_session(
    sessions: SessionsDep,
    users: UsersDep,
    tokens: TokensDep,
    issuer: IssuerDep,
    clock: ClockDep,
    uow: UowDep,
) -> RefreshSession:
    return RefreshSession(sessions, users, tokens, issuer, clock, uow)


def get_logout_user(
    sessions: SessionsDep, tokens: TokensDep, clock: ClockDep, uow: UowDep
) -> LogoutUser:
    return LogoutUser(sessions, tokens, clock, uow)


def get_authenticate_access_token(
    sessions: SessionsDep, users: UsersDep, tokens: TokensDep, clock: ClockDep
) -> AuthenticateAccessToken:
    return AuthenticateAccessToken(sessions, users, tokens, clock)


def build_purge_expired_sessions(
    session: AsyncSession, cache: CacheClient, settings: Settings
) -> PurgeExpiredSessions:
    """Used by the background retention task, which has no request to hang off."""
    clock = SystemClock()
    sessions = CachedSessionRepository(
        SqlSessionRepository(session),
        cache,
        clock,
        ttl_seconds=settings.cache_ttl_seconds,
    )
    return PurgeExpiredSessions(
        sessions,
        clock,
        CacheAwareUnitOfWork(session, sessions.invalidation),
        retention=timedelta(days=settings.session_retention_days),
    )


# --- current user ------------------------------------------------------------

bearer_scheme = HTTPBearer(auto_error=False)
BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_access_token(credentials: BearerDep) -> str:
    if credentials is None or not credentials.credentials.strip():
        raise InvalidToken("Authorization header is missing")
    return credentials.credentials


AccessTokenDep = Annotated[str, Depends(get_access_token)]


async def get_current_user(
    access_token: AccessTokenDep,
    authenticate: Annotated[AuthenticateAccessToken, Depends(get_authenticate_access_token)],
) -> AuthenticatedUser:
    return await authenticate.execute(access_token)


CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]


# --- project use cases -------------------------------------------------------


def get_create_project(projects: ProjectsDep, clock: ClockDep, uow: UowDep) -> CreateProject:
    return CreateProject(projects, clock, uow)


def get_list_projects(projects: ProjectsDep) -> ListProjects:
    return ListProjects(projects)


def get_update_project(projects: ProjectsDep, clock: ClockDep, uow: UowDep) -> UpdateProject:
    return UpdateProject(projects, clock, uow)


def get_delete_project(projects: ProjectsDep, uow: UowDep) -> DeleteProject:
    return DeleteProject(projects, uow)


# --- time entry use cases ----------------------------------------------------


def get_start_timer(
    entries: EntriesDep, projects: ProjectsDep, clock: ClockDep, uow: UowDep
) -> StartTimer:
    return StartTimer(entries, projects, clock, uow)


def get_stop_timer(entries: EntriesDep, clock: ClockDep, uow: UowDep) -> StopTimer:
    return StopTimer(entries, clock, uow)


def get_running_timer(entries: EntriesDep) -> GetRunningTimer:
    return GetRunningTimer(entries)


def get_list_time_entries(entries: EntriesDep) -> ListTimeEntries:
    return ListTimeEntries(entries)


def get_create_time_entry(
    entries: EntriesDep, projects: ProjectsDep, clock: ClockDep, uow: UowDep
) -> CreateTimeEntry:
    return CreateTimeEntry(entries, projects, clock, uow)


def get_update_time_entry(
    entries: EntriesDep, projects: ProjectsDep, clock: ClockDep, uow: UowDep
) -> UpdateTimeEntry:
    return UpdateTimeEntry(entries, projects, clock, uow)


def get_delete_time_entry(entries: EntriesDep, uow: UowDep) -> DeleteTimeEntry:
    return DeleteTimeEntry(entries, uow)
