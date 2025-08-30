import abc

from src.dto.user import CreateUserTokenPayload
from src.models.user import UserTokenModel


class UserTokenUseCase(abc.ABC):

    @abc.abstractmethod
    async def create_token(self, payload: CreateUserTokenPayload) -> UserTokenModel:
        ...

    @abc.abstractmethod
    async def check_token_is_exists(self, token: str) -> bool:
        ...

    @abc.abstractmethod
    async def get_token(self, token: str) -> UserTokenModel:
        ...

