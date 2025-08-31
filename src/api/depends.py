from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader

from src.config import app_config
from src.models.user import UserModel
from src.repository.user import UserRepositoryDB
from src.repository.user_token import UserTokenRepositoryDB
from src.service.user_auth import UserAuthService
from src.use_case.user import UserUseCase
from src.use_case.user_tokens import UserTokenUseCase

app = FastAPI()
header_scheme = APIKeyHeader(name="User-Token")


def service_user_auth_depends(
    user_repository: UserUseCase = Depends(UserRepositoryDB),
    token_repository: UserTokenUseCase = Depends(UserTokenRepositoryDB),
) -> UserAuthService:
    return UserAuthService(
        user_repository=user_repository,
        token_repository=token_repository,
        tokens_expirations_days=app_config.app.tokens_expirations_days,
        hash_salt=app_config.app.hash_salt,
    )

async def check_authorization_token(
    token: str = Depends(header_scheme),
    auth_user_service: UserAuthService = Depends(service_user_auth_depends),
) -> UserModel:
    result = await auth_user_service.check_token(token)
    if isinstance(result, Exception):
        raise result
    else:
        return result

