from typing import Any, AsyncGenerator

from aiocache import BaseCache
from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader

from src.cache import AppCacher
from src.config import app_config
from src.models.user import UserModel
from src.repository.user import UserRepositoryDB
from src.repository.user_token import UserTokenRepositoryDB
from src.service.user import UserService
from src.service.user_auth import UserAuthService
from src.use_case.user import UserUseCase
from src.use_case.user_tokens import UserTokenUseCase

app = FastAPI()
header_scheme = APIKeyHeader(name="User-Token")


async def cacher_depends() -> AsyncGenerator[BaseCache, Any]:
    async with AppCacher.cacher_factory() as cache:
        yield cache

def service_user_auth_depends(
    user_repository: UserUseCase = Depends(UserRepositoryDB),
    token_repository: UserTokenUseCase = Depends(UserTokenRepositoryDB),
    cacher: BaseCache = Depends(cacher_depends),
) -> UserAuthService:
    return UserAuthService(
        user_repository=user_repository,
        token_repository=token_repository,
        tokens_expirations_days=app_config.app.tokens_expirations_days,
        hash_salt=app_config.app.hash_salt,
    )

def service_user_depends(user_repository: UserUseCase = Depends(UserRepositoryDB)) -> UserService:
    return UserService(user_repository=user_repository)

async def check_user_token(
    token: str = Depends(header_scheme),
    auth_user_service: UserAuthService = Depends(service_user_auth_depends),
) -> UserModel:
    return await auth_user_service.check_token(token)

