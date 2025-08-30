from sqlalchemy import exists, select

from src.database.converter import DatabaseModelsConverter
from src.database.orm import UserORM
from src.dto.user import CreateUserPayload, UpdateUserPayload
from src.exceptions import DataUniqueError, NotFoundError
from src.models.user import UserModel
from src.use_case.user import UserUseCase

from .mixin import DatabaseRepositoryMixin


class UserRepositoryDB(DatabaseRepositoryMixin, UserUseCase):

    async def _get_orm_by_id(self, user_id: int, return_deleted: bool = False) -> UserORM:
        query = select(UserORM).filter_by(id=user_id)
        if not return_deleted:
            query.filter_by(deleted=False)

        result = await self.session.execute(query)
        user_orm = result.scalar()
        if user_orm is None:
            raise NotFoundError(10, "User not found", "User not found in database by id")

        return user_orm

    async def create_user(self, payload: CreateUserPayload) -> UserModel:
        result = await self.session.execute(
            exists().where(UserORM.username == payload.username).select(),
        )
        if result.scalar():
            raise DataUniqueError(
                11,
                "User with that username already exists",
                f"User with username={payload.username} already exists in database",
            )

        user_orm = UserORM(
            username=payload.username,
            display_name=payload.display_name,
            pass_hash=payload.pass_hash,
        )
        self.session.add(user_orm)
        await self.session.commit()
        await self.session.refresh(user_orm)
        return DatabaseModelsConverter.user_orm_to_model(user_orm)

    async def get_by_id(self, user_id: int, return_deleted: bool = False) -> UserModel:
        user_orm = await self._get_orm_by_id(user_id, return_deleted)
        return DatabaseModelsConverter.user_orm_to_model(user_orm)

    async def get_by_username(self, username: str) -> UserModel:
        result = await self.session.execute(select(UserORM).filter_by(username=username))
        user_orm = result.scalar()
        if user_orm is None:
            raise NotFoundError(12, "User not found", "User not found in database by username")
        return DatabaseModelsConverter.user_orm_to_model(user_orm)

    async def update_user(self, payload: UpdateUserPayload) -> UserModel:
        result = await self.session.execute(
            exists().where(
                UserORM.username == payload.username and UserORM.id != payload.user_id,
            ).select(),
        )
        if result.scalar():
            raise DataUniqueError(
                13,
                "User with that username already exists",
                f"User with username={payload.username} already exists in database",
            )

        user_orm = await self._get_orm_by_id(payload.user_id)
        user_orm.username = payload.username
        await self.session.commit()
        await self.session.refresh(user_orm)
        return DatabaseModelsConverter.user_orm_to_model(user_orm)

    async def delete_user(self, user_id: int) -> None:
        user_orm = await self._get_orm_by_id(user_id)
        user_orm.deleted = True
        await self.session.commit()

