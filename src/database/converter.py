from src.database.orm.organization import OrganizationORM
from src.database.orm.user import UserORM
from src.database.orm.user_token import UserTokenORM
from src.models.organization import OrganizationModel
from src.models.user import UserModel, UserTokenModel


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

