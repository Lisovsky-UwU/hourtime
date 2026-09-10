"""Turns Postgres constraint violations into domain errors.

A lost race (two tabs starting a timer, two signups with the same email) must
read the same to the caller as losing the check that precedes it.
"""

from collections.abc import Awaitable, Callable

from sqlalchemy.exc import IntegrityError

from hourtime.domain.errors import (
    DomainError,
    EmailAlreadyUsed,
    ProjectNameTaken,
    TimerAlreadyRunning,
)

_BY_CONSTRAINT: dict[str, type[DomainError]] = {
    "users_email_key": EmailAlreadyUsed,
    "uq_projects_user_active_name": ProjectNameTaken,
    "uq_time_entries_one_running": TimerAlreadyRunning,
}


def _constraint_of(error: IntegrityError) -> str | None:
    diagnostics = getattr(getattr(error, "orig", None), "diag", None)
    name = getattr(diagnostics, "constraint_name", None)
    return str(name) if name else None


async def translating_integrity_errors[T](operation: Callable[[], Awaitable[T]]) -> T:
    try:
        return await operation()
    except IntegrityError as error:
        constraint = _constraint_of(error)
        mapped = _BY_CONSTRAINT.get(constraint or "")
        if mapped is None:
            raise
        raise mapped from error
