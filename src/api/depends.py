from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader

from src.config import app_config
from src.models.user import UserModel
from src.repository.organization import OrganizationRepositoryDB
from src.repository.project import ProjectRepositoryDB
from src.repository.task import TaskRepositoryDB
from src.repository.time_entry import TimeEntryRepositoryDB
from src.repository.user import UserRepositoryDB
from src.repository.user_token import UserTokenRepositoryDB
from src.repository.workspace import WorkspaceRepositoryDB
from src.service.organization import OrganizationService
from src.service.project import ProjectService
from src.service.task import TaskService
from src.service.time_entry import TimeEntryService
from src.service.user import UserService
from src.service.user_auth import UserAuthService
from src.service.workspace import WorkspaceService
from src.use_case.organization import OrganizationUseCase
from src.use_case.project import ProjectUseCase
from src.use_case.task import TaskUseCase
from src.use_case.time_entry import TimeEntryUseCase
from src.use_case.user import UserUseCase
from src.use_case.user_tokens import UserTokenUseCase
from src.use_case.workspace import WorkspaceUseCase

app = FastAPI()
token_header_scheme = APIKeyHeader(name="User-Token")


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

def service_user_depends(user_repository: UserUseCase = Depends(UserRepositoryDB)) -> UserService:
    return UserService(user_repository=user_repository)

def service_organization_depends(
    organization_repository: OrganizationUseCase = Depends(OrganizationRepositoryDB),
    workspace_repository: WorkspaceUseCase = Depends(WorkspaceRepositoryDB),
) -> OrganizationService:
    return OrganizationService(organization_repository, workspace_repository)

def service_workspace_depends(
    workspace_repository: WorkspaceUseCase = Depends(WorkspaceRepositoryDB),
    organization_repository: OrganizationUseCase = Depends(OrganizationRepositoryDB),
) -> WorkspaceService:
    return WorkspaceService(workspace_repository, organization_repository)

def service_project_depends(
    project_repository: ProjectUseCase = Depends(ProjectRepositoryDB),
    workspace_repository: WorkspaceUseCase = Depends(WorkspaceRepositoryDB),
) -> ProjectService:
    return ProjectService(project_repository, workspace_repository)

def service_task_depends(
    task_repository: TaskUseCase = Depends(TaskRepositoryDB),
    workspace_repository: WorkspaceUseCase = Depends(WorkspaceRepositoryDB),
) -> TaskService:
    return TaskService(task_repository, workspace_repository)

def service_time_entry_depends(
    time_entry_repository: TimeEntryUseCase = Depends(TimeEntryRepositoryDB),
    workspace_repository: WorkspaceUseCase = Depends(WorkspaceRepositoryDB),
) -> TimeEntryService:
    return TimeEntryService(time_entry_repository, workspace_repository)

async def check_user_token(
    token: str = Depends(token_header_scheme),
    auth_user_service: UserAuthService = Depends(service_user_auth_depends),
) -> UserModel:
    return await auth_user_service.check_token(token)

