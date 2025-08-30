from src.database.orm.organization import OrganizationORM
from src.database.orm.user import UserORM
from src.models.organization import OrganizationModel
from src.models.user import UserModel


class DatabaseModelsConverter:

    @staticmethod
    def user_orm_to_model(user_orm: UserORM) -> UserModel:
        return UserModel(
            id=user_orm.id,
            username=user_orm.username,
            display_name=user_orm.display_name,
            pass_hash=user_orm.pass_hash,
        )

    @staticmethod
    def organization_orm_to_model(organization_orm: OrganizationORM) -> OrganizationModel:
        return OrganizationModel(
            id=organization_orm.id,
            name=organization_orm.name,
        )

