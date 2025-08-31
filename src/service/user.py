from src.dto.api.user import UpdateUserRequest
from src.dto.user import UpdateUserPayload
from src.models.user import UserModel
from src.use_case.user import UserUseCase


class UserService:

    def __init__(self, user_repository: UserUseCase) -> None:
        self.user_repository = user_repository

    async def update_user_data(self, user_id: int, payload: UpdateUserRequest) -> UserModel:
        return await self.user_repository.update_user(UpdateUserPayload(
            user_id=user_id,
            username=payload.username,
            display_name=payload.display_name,
        ))

