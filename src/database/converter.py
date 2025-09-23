from src.database.orm.organization import OrganizationORM
from src.database.orm.project import ProjectORM
from src.database.orm.task import TaskORM
from src.database.orm.time_entry import TimeEntryORM
from src.database.orm.user import UserORM
from src.database.orm.user_token import UserTokenORM
from src.database.orm.workspace import WorkspaceORM
from src.dto.organization import UserOrganizationWithWorkspaces
from src.dto.time_entry import TimeEntryForUser
from src.dto.workspace import WorkspaceSubElement
from src.models.common import UserAccess
from src.models.organization import OrganizationModel
from src.models.project import ProjectModel
from src.models.task import TaskModel
from src.models.time_entery import TimeEntryModel
from src.models.user import UserModel, UserTokenModel
from src.models.workspace import WorkspaceModel


class DatabaseModelsConverter:

    @staticmethod
    def user_orm_to_model(user_orm: UserORM) -> UserModel:
        return UserModel(
            id=user_orm.id,
            username=user_orm.username,
            display_name=user_orm.display_name,
            pass_hash=user_orm.pass_hash,
        )

    @classmethod
    def user_token_orm_to_model(cls, token_orm: UserTokenORM) -> UserTokenModel:
        return UserTokenModel(
            id=token_orm.id,
            user_id=token_orm.user_id,
            token=token_orm.token,
            created_at=token_orm.created_at,
        )

    @staticmethod
    def organization_orm_to_model(organization_orm: OrganizationORM) -> OrganizationModel:
        return OrganizationModel(
            id=organization_orm.id,
            name=organization_orm.name,
        )

    @staticmethod
    def organization_orm_for_user_with_workspace(
        organization_orm: OrganizationORM,
        access: UserAccess,
    ) -> UserOrganizationWithWorkspaces:
        """
        Must call after `await self.session.refresh(organization_orm, ["workspaces"])`.
        """
        return UserOrganizationWithWorkspaces(
            organization_id=organization_orm.id,
            name=organization_orm.name,
            access=access,
            workspaces=[
                WorkspaceSubElement(
                    id=workspace.id,
                    name=workspace.name,
                )
                for workspace in organization_orm.workspaces if not workspace.deleted
            ],
        )

    @staticmethod
    def workspace_orm_to_model(workspace_orm: WorkspaceORM) -> WorkspaceModel:
        return WorkspaceModel(
            id=workspace_orm.id,
            organization_id=workspace_orm.organization_id,
            name=workspace_orm.name,
        )

    @staticmethod
    def project_orm_to_model(project_orm: ProjectORM) -> ProjectModel:
        return ProjectModel(
            id=project_orm.id,
            workspace_id=project_orm.workspace_id,
            name=project_orm.name,
            description=project_orm.description,
        )

    @staticmethod
    def task_orm_to_model(task_orm: TaskORM) -> TaskModel:
        return TaskModel(
            id=task_orm.id,
            number=task_orm.number,
            name=task_orm.name,
            description=task_orm.description,
            project_id=task_orm.project_id,
            workspace_id=task_orm.workspace_id,
        )

    @staticmethod
    def time_entry_orm_to_model(time_entry_orm: TimeEntryORM) -> TimeEntryModel:
        return TimeEntryModel(
            id=time_entry_orm.id,
            user_id=time_entry_orm.user_id,
            comment=time_entry_orm.comment,
            workspace_id=time_entry_orm.workspace_id,
            project_id=time_entry_orm.project_id,
            task_id=time_entry_orm.task_id,
            start_date=time_entry_orm.start_date,
            start_time=time_entry_orm.start_time,
            end_date=time_entry_orm.end_date,
            end_time=time_entry_orm.end_time,
        )

    @staticmethod
    def time_entry_orm_to_model_for_user(time_entry_orm: TimeEntryORM) -> TimeEntryForUser:
        return TimeEntryForUser(
            id=time_entry_orm.id,
            comment=time_entry_orm.comment,
            workspace_id=time_entry_orm.workspace_id,
            project_id=time_entry_orm.project_id,
            task_id=time_entry_orm.task_id,
            start_date=time_entry_orm.start_date,
            start_time=time_entry_orm.start_time,
            end_date=time_entry_orm.end_date,
            end_time=time_entry_orm.end_time,
        )

