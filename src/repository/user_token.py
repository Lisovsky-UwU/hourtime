from sqlalchemy import delete, exists, select

from src.cache_constants import CacheConst
from src.database.converter import DatabaseModelsConverter
from src.database.orm.user_token import UserTokenORM
from src.dto.user import CreateUserTokenPayload
from src.exceptions import NotFoundError
from src.models.user import UserTokenModel
from src.repository.mixin import DatabaseRepositoryMixin
from src.use_case.user_tokens import UserTokenUseCase


class UserTokenRepositoryDB(DatabaseRepositoryMixin, UserTokenUseCase):

    async def create_token(self, payload: CreateUserTokenPayload) -> UserTokenModel:
        token_orm = UserTokenORM(
            user_id=payload.user_id,
            token=payload.token,
        )
        self.session.add(token_orm)
        await self.session.commit()
        await self.session.refresh(token_orm)
        token_model = DatabaseModelsConverter.user_token_orm_to_model(token_orm)
        await self.cacher.set(
            CacheConst.User.AuthToken.format(token_model.token),
            token_model,
            ttl=300,
        )
        return token_model

    async def check_token_is_exists(self, token: str) -> bool:
        result = await self.session.execute(
            exists().where(UserTokenORM.token == token).select(),
        )
        return result.scalar() or False

    async def get_token(self, token: str) -> UserTokenModel:
        token_cache_key = CacheConst.User.AuthToken.format(token)

        token_model: UserTokenModel | NotFoundError | None = await self.cacher.get(token_cache_key)
        if token_model is not None and isinstance(token_model, NotFoundError):
            raise token_model

        elif token_model is None:
            result = await self.session.execute(
                select(UserTokenORM).filter_by(token = token),
            )
            token_orm = result.scalar()
            if token_orm is None:
                exception = NotFoundError(15, "Token not found", "Cannot find token")
                await self.cacher.set(token_cache_key, exception, ttl=300)
                raise exception

            token_model = DatabaseModelsConverter.user_token_orm_to_model(token_orm)
            await self.cacher.set(token_cache_key, token_model, ttl=300)

        return token_model

    async def delete_token(self, token: str) -> None:
        query = delete(UserTokenORM).filter_by(token=token)
        await self.session.execute(query)
        await self.session.commit()
        await self.cacher.delete(CacheConst.User.AuthToken.format(token))

