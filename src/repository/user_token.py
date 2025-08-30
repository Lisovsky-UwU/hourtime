from sqlalchemy import exists, select

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
        return DatabaseModelsConverter.user_token_orm_to_model(token_orm)

    async def check_token_is_exists(self, token: str) -> bool:
        result = await self.session.execute(
            exists().where(UserTokenORM.token == token).select(),
        )
        return result.scalar() or False

    async def get_token(self, token: str) -> UserTokenModel:
        result = await self.session.execute(
            select(UserTokenORM).filter_by(token = token),
        )
        token_orm = result.scalar()
        if token_orm is None:
            raise NotFoundError(15, "Token not found", "Cannot find token")

        return DatabaseModelsConverter.user_token_orm_to_model(token_orm)

