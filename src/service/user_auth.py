import secrets
from datetime import datetime, timedelta

from aiocache import cached
from aiocache.serializers import PickleSerializer

from src.dto.api.user import UserLoginRequest, UserRegisteringRequest
from src.dto.user import CreateUserPayload, CreateUserTokenPayload
from src.exceptions import AuthentificationError, NotFoundError
from src.models.user import UserModel, UserTokenModel
from src.use_case.user import UserUseCase
from src.use_case.user_tokens import UserTokenUseCase
from src.utils import calculate_hash


class UserAuthService:

    def __init__(
        self, user_repository: UserUseCase,
        token_repository: UserTokenUseCase,
        tokens_expirations_days: int,
        hash_salt: str,
    ) -> None:
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.tokens_expirations_days = tokens_expirations_days
        self.hash_salt = hash_salt

    async def generate_token(self, user_id: int) -> UserTokenModel:
        while True:
            str_token = secrets.token_hex(32)
            if not await self.token_repository.check_token_is_exists(str_token):
                break
        token_model = await self.token_repository.create_token(CreateUserTokenPayload(
            user_id=user_id,
            token=str_token,
        ))
        return token_model

    async def registrate_user(self, payload: UserRegisteringRequest) -> UserTokenModel:
        pass_hash = calculate_hash(payload.password, self.hash_salt)
        user_model = await self.user_repository.create_user(CreateUserPayload(
            username=payload.username,
            display_name=payload.display_name,
            pass_hash=pass_hash,
        ))
        return await self.generate_token(user_model.id)

    async def login_user(self, payload: UserLoginRequest) -> UserTokenModel:
        try:
            user_model = await self.user_repository.get_by_username(payload.username)
            pass_hash = calculate_hash(payload.password, self.hash_salt)
            if pass_hash != user_model.pass_hash:
                raise AuthentificationError(14, "Cannot login", "Username or password is incorrect")
            return await self.generate_token(user_model.id)
        except NotFoundError as exc:
            raise AuthentificationError(
                14,
                "Cannot login",
                "Username or password is incorrect",
            ) from exc

    @cached(ttl=300, serializer=PickleSerializer())
    async def check_token(self, token: str) -> UserModel | AuthentificationError:
        try:
            token_model = await self.token_repository.get_token(token)
        except NotFoundError:
            return AuthentificationError(
                15,
                "Invalid token",
                "Given token was not found or expired.",
            )
        token_expiration_date = token_model.created_at + timedelta(
            days=self.tokens_expirations_days,
        )
        if datetime.now() > token_expiration_date:
            return AuthentificationError(
                15,
                "Invalid token",
                "The transferred token was not found or expired.",
            )
        return token_model.user

