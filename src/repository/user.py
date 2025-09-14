from sqlalchemy import and_, exists, select

from src.cache_constants import CacheConst
from src.database.converter import DatabaseModelsConverter
from src.database.orm import UserORM
from src.dto.user import CreateUserPayload, UpdateUserPayload
from src.exceptions import DataUniqueError, NotFoundError
from src.models.user import UserModel
from src.use_case.user import UserUseCase

from .mixin import DatabaseRepositoryMixin


class UserRepositoryDB(DatabaseRepositoryMixin, UserUseCase):

    async def _get_orm_by_id(self, user_id: int, return_deleted: bool = False) -> UserORM:
        filter_ = UserORM.id == user_id
        if not return_deleted:
            filter_ = and_(filter_, UserORM.deleted == False)  # noqa: E712

        query = select(UserORM).filter(filter_)

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
        user_model = DatabaseModelsConverter.user_orm_to_model(user_orm)
        await self.cacher.set(CacheConst.User.Model.ById.format(user_model.id), user_model, ttl=300)
        return user_model

    async def get_by_id(self, user_id: int, return_deleted: bool = False) -> UserModel:
        user_cache_key = CacheConst.User.Model.ById.format(user_id)

        user_model: UserModel | NotFoundError | None = await self.cacher.get(user_cache_key)
        if user_model is not None and isinstance(user_model, NotFoundError):
            raise user_model
        elif user_model is None:
            try:
                user_orm = await self._get_orm_by_id(user_id, return_deleted)
            except NotFoundError as exc:
                await self.cacher.set(user_cache_key, exc, ttl=300)
                raise exc

            user_model = DatabaseModelsConverter.user_orm_to_model(user_orm)
            await self.cacher.set(user_cache_key, user_model, ttl=300)

        return user_model

    async def get_by_username(self, username: str) -> UserModel:
        result = await self.session.execute(select(UserORM).filter_by(username=username))
        user_orm = result.scalar()
        if user_orm is None:
            raise NotFoundError(12, "User not found", "User not found in database by username")
        return DatabaseModelsConverter.user_orm_to_model(user_orm)

    async def update_user(self, payload: UpdateUserPayload) -> UserModel:
        result = await self.session.execute(
            exists().where(
                UserORM.username == payload.username, UserORM.id != payload.user_id,
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
        user_orm.display_name = payload.display_name
        await self.session.commit()
        await self.session.refresh(user_orm)
        user_model = DatabaseModelsConverter.user_orm_to_model(user_orm)
        await self.cacher.set(CacheConst.User.Model.ById.format(user_model.id), user_model, ttl=300)
        return user_model

    async def update_user_pass_hash(self, user_id: int, new_pass_hash: str) -> None:
        user_orm = await self._get_orm_by_id(user_id)
        user_orm.pass_hash = new_pass_hash
        await self.session.commit()
        await self.session.refresh(user_orm)
        user_model = DatabaseModelsConverter.user_orm_to_model(user_orm)
        await self.cacher.set(CacheConst.User.Model.ById.format(user_model.id), user_model, ttl=300)

    async def delete_user(self, user_id: int) -> None:
        user_orm = await self._get_orm_by_id(user_id)
        user_orm.deleted = True
        await self.session.commit()
        await self.cacher.delete(CacheConst.User.Model.ById.format(user_id))

