from sqlalchemy import select

from src.database.converter import DatabaseModelsConverter
from src.database.orm import OrganizationORM
from src.database.orm.link_user_organization import LinkUserOrganizationORM
from src.dto.organization import (
    AddUserToOrganizationPayload,
    CreateOrganizationPayload,
    UpdateOrganizationPayload,
)
from src.exceptions import NotFoundError
from src.models.common import UserAccess
from src.models.organization import OrganizationModel, UserOrganizationModel
from src.use_case.organization import OrganizationUseCase

from .mixin import DatabaseRepositoryMixin


class OrganizationRepositoryDB(DatabaseRepositoryMixin, OrganizationUseCase):

    async def _get_orm_by_id(
        self,
        organization_id: int,
        return_deleted: bool = False,
    ) -> OrganizationORM:
        query = select(OrganizationORM).filter_by(id=organization_id)
        if not return_deleted:
            query.filter_by(deleted=False)

        result = await self.session.execute(query)
        user_orm = result.scalar()
        if user_orm is None:
            raise NotFoundError(
                20,
                "Organization not found",
                "Organization not found in database by id",
            )

        return user_orm


    async def create_organization(self, payload: CreateOrganizationPayload) -> OrganizationModel:
        organization_orm = OrganizationORM(name=payload.name)
        self.session.add(organization_orm)
        await self.session.commit()
        await self.session.refresh(organization_orm)
        return DatabaseModelsConverter.organization_orm_to_model(organization_orm)

    async def add_users_to_organization(
        self,
        payload: AddUserToOrganizationPayload,
    ) -> OrganizationModel:
        organization_orm = await self._get_orm_by_id(payload.organization_id)
        # Use a link because relations addition/deletion creates duplicates
        for link in payload.users:
            link_user_orm = LinkUserOrganizationORM(
                user_id=link.user_id,
                organization_id=organization_orm.id,
                access=link.access,
            )
            self.session.add(link_user_orm)
        await self.session.commit()
        await self.session.refresh(organization_orm)
        return DatabaseModelsConverter.organization_orm_to_model(organization_orm)

    async def get_user_organizations(self, user_id: int) -> list[UserOrganizationModel]:
        query = (
            select(OrganizationORM.id, OrganizationORM.name, LinkUserOrganizationORM.access)
            .join(
                LinkUserOrganizationORM,
                LinkUserOrganizationORM.organization_id == OrganizationORM.id,
            )
            .filter(OrganizationORM.deleted == False, LinkUserOrganizationORM.user_id == user_id)  # noqa: E712
        )
        result = await self.session.execute(query)
        response: list[UserOrganizationModel] = []
        for row in result:
            response.append(
                UserOrganizationModel(
                    organization_id=row[0],
                    organization_name=row[1],
                    access=row[2],
                ),
            )

        return response

    async def get_user_access_in_organization(
        self,
        user_id: int,
        organization_id: int,
    ) -> UserAccess | None:
        query = (
            select(LinkUserOrganizationORM.access)
            .select_from(OrganizationORM)
            .join(
                LinkUserOrganizationORM,
                LinkUserOrganizationORM.organization_id == OrganizationORM.id,
            )
            .filter(
                OrganizationORM.deleted == False,  # noqa: E712
                LinkUserOrganizationORM.user_id == user_id,
                LinkUserOrganizationORM.organization_id == organization_id,
            )
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def update_organization(self, payload: UpdateOrganizationPayload) -> OrganizationModel:
        organization_orm = await self._get_orm_by_id(payload.organization_id)
        organization_orm.name = payload.name
        await self.session.commit()
        await self.session.refresh(organization_orm)
        return DatabaseModelsConverter.organization_orm_to_model(organization_orm)

    async def delete_organization(self, organization_id: int) -> None:
        organization_orm = await self._get_orm_by_id(organization_id)
        organization_orm.deleted = True
        await self.session.commit()

