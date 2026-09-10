from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.domain.entities import User
from hourtime.domain.errors import NotFound
from hourtime.infrastructure.db.models import UserModel
from hourtime.infrastructure.db.repositories.integrity import translating_integrity_errors
from hourtime.interfaces.repositories import UserRepository


def to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        password_hash=model.password_hash,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        statement = sa.select(UserModel).where(UserModel.email == email.strip().lower())
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return to_domain(model) if model else None

    async def add(self, user: User) -> User:
        model = UserModel(**user.model_dump())
        self._session.add(model)
        # Flush here so a duplicate email surfaces as EmailAlreadyUsed instead
        # of blowing up later at commit time.
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def update(self, user: User) -> User:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            raise NotFound("User not found")
        for field, value in user.model_dump().items():
            setattr(model, field, value)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)
