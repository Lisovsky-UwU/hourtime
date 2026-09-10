from datetime import datetime
from typing import Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.domain.entities import Session
from hourtime.domain.errors import NotFound
from hourtime.infrastructure.db.models import SessionModel
from hourtime.infrastructure.db.repositories.integrity import translating_integrity_errors
from hourtime.interfaces.repositories import SessionRepository


def to_domain(model: SessionModel) -> Session:
    return Session(
        id=model.id,
        user_id=model.user_id,
        access_token_hash=model.access_token_hash,
        refresh_token_hash=model.refresh_token_hash,
        access_expires_at=model.access_expires_at,
        refresh_expires_at=model.refresh_expires_at,
        revoked_at=model.revoked_at,
        created_at=model.created_at,
        last_used_at=model.last_used_at,
        user_agent=model.user_agent,
        ip=model.ip,
    )


class SqlSessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_access_token_hash(self, token_hash: str) -> Session | None:
        statement = sa.select(SessionModel).where(SessionModel.access_token_hash == token_hash)
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return to_domain(model) if model else None

    async def get_by_refresh_token_hash(self, token_hash: str) -> Session | None:
        statement = sa.select(SessionModel).where(SessionModel.refresh_token_hash == token_hash)
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return to_domain(model) if model else None

    async def add(self, session: Session) -> Session:
        model = SessionModel(**session.model_dump())
        self._session.add(model)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def update(self, session: Session) -> Session:
        model = await self._session.get(SessionModel, session.id)
        if model is None:
            raise NotFound("Session not found")
        for field, value in session.model_dump().items():
            setattr(model, field, value)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def active_access_hashes(self, user_id: UUID) -> list[str]:
        """Access digests of the user's live sessions.

        Not part of `SessionRepository` — the caching decorator uses it to know
        which keys a bulk revoke invalidates.
        """
        statement = sa.select(SessionModel.access_token_hash).where(
            SessionModel.user_id == user_id, SessionModel.revoked_at.is_(None)
        )
        return list((await self._session.execute(statement)).scalars().all())

    async def revoke_all_for_user(self, user_id: UUID, at: datetime) -> int:
        statement = (
            sa.update(SessionModel)
            .where(SessionModel.user_id == user_id, SessionModel.revoked_at.is_(None))
            .values(revoked_at=at)
            .execution_options(synchronize_session=False)
        )
        result = cast(CursorResult[Any], await self._session.execute(statement))
        return result.rowcount

    async def delete_expired_before(self, cutoff: datetime) -> int:
        statement = (
            sa.delete(SessionModel)
            .where(SessionModel.refresh_expires_at < cutoff)
            .execution_options(synchronize_session=False)
        )
        result = cast(CursorResult[Any], await self._session.execute(statement))
        return result.rowcount
