import abc

from src.dto.user import CreateUserPayload, UpdateUserPayload
from src.models.user import UserModel


class UserUseCase(abc.ABC):

    @abc.abstractmethod
    async def create_user(self, payload: CreateUserPayload) -> UserModel:
        ...

    @abc.abstractmethod
    async def get_by_id(self, user_id: int, return_deleted: bool = False) -> UserModel:
        ...

    @abc.abstractmethod
    async def get_by_username(self, username: str) -> UserModel:
        ...

    @abc.abstractmethod
    async def update_user(self, payload: UpdateUserPayload) -> UserModel:
        ...

    @abc.abstractmethod
    async def delete_user(self, user_id: int) -> None:
        ...

