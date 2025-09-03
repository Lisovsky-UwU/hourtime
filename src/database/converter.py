from src.database.orm.organization import OrganizationORM
from src.database.orm.user import UserORM
from src.database.orm.user_token import UserTokenORM
from src.database.orm.workspace import WorkspaceORM
from src.dto.organization import UserOrganizationWithWorkspaces
from src.dto.workspace import WorkspaceSubElement
from src.models.common import UserAccess
from src.models.organization import OrganizationModel
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
                for workspace in organization_orm.workspaces
            ],
        )

    @staticmethod
    def workspace_orm_to_model(workspace_orm: WorkspaceORM) -> WorkspaceModel:
        return WorkspaceModel(
            id=workspace_orm.id,
            organization_id=workspace_orm.organization_id,
            name=workspace_orm.name,
        )

