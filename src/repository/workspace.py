from sqlalchemy import and_, select

from src.cache_constants import CacheConst
from src.database.converter import DatabaseModelsConverter
from src.database.orm.link_user_organization import LinkUserOrganizationORM
from src.database.orm.organization import OrganizationORM
from src.database.orm.workspace import WorkspaceORM
from src.dto.workspace import CreateWorkspacePayload, UpdateWorkspacePayload
from src.exceptions import NotFoundError
from src.models.common import UserAccess
from src.models.workspace import WorkspaceModel
from src.repository.mixin import DatabaseRepositoryMixin
from src.use_case.workspace import WorkspaceUseCase


class WorkspaceRepositoryDB(DatabaseRepositoryMixin, WorkspaceUseCase):

    async def _get_orm_by_id(self, workspace_id: int, return_deleted: bool = False) -> WorkspaceORM:
        filter_ = WorkspaceORM.id == workspace_id
        if not return_deleted:
            filter_ = and_(filter_, WorkspaceORM.deleted == False)  # noqa: E712

        query = select(WorkspaceORM).filter(filter_)
        result = await self.session.execute(query)
        user_orm = result.scalar()
        if user_orm is None:
            raise NotFoundError(30, "Workspace not found", "Workspace not found in database by id")

        return user_orm

    async def _get_organization_id_and_user_access(
        self,
        user_id: int,
        workspace_id: int,
    ) -> tuple[int, UserAccess] | tuple[None, None]:
        query = (
            select(WorkspaceORM.organization_id, LinkUserOrganizationORM.access)
            .select_from(WorkspaceORM)
            .join(
                OrganizationORM,
                OrganizationORM.id == WorkspaceORM.organization_id,
            )
            .join(
                LinkUserOrganizationORM,
                LinkUserOrganizationORM.organization_id == OrganizationORM.id,
            )
            .filter(
                WorkspaceORM.id == workspace_id,
                WorkspaceORM.deleted == False,  # noqa: E712
                OrganizationORM.deleted == False,  # noqa: E712
                LinkUserOrganizationORM.user_id == user_id,
            )
        )
        result = await self.session.execute(query)
        row = result.first()
        if row is not None:
            value = row.tuple()
        else:
            value = None, None

        return value

    async def create_workspace(self, payload: CreateWorkspacePayload) -> WorkspaceModel:
        workspace_orm = WorkspaceORM(
            name=payload.name,
            organization_id=payload.organization_id,
        )
        self.session.add(workspace_orm)
        await self.session.commit()
        await self.session.refresh(workspace_orm)
        await self._clear_cache_for_organization(workspace_orm.organization_id)
        return DatabaseModelsConverter.workspace_orm_to_model(workspace_orm)

    async def get_by_organization(self, organization_id: int) -> list[WorkspaceModel]:
        query = (
            select(WorkspaceORM)
            .filter(WorkspaceORM.organization_id == organization_id, WorkspaceORM.deleted == False)  # noqa: E712
        )
        result = await self.session.execute(query)
        response: list[WorkspaceModel] = []
        for row in result.scalars():
            response.append(DatabaseModelsConverter.workspace_orm_to_model(row))

        return response

    async def get_workspace_by_id(
        self,
        workspace_id: int,
        return_deleted: bool = False,
    ) -> WorkspaceModel:
        return DatabaseModelsConverter.workspace_orm_to_model(
            await self._get_orm_by_id(workspace_id, return_deleted),
        )

    async def get_user_access(self, user_id: int, workspace_id: int) -> UserAccess | None:
        key_organization = CacheConst.Workspace.WorkspaceOrganization.format(workspace_id)
        key_workspace_user_access = CacheConst.Workspace.WorkspaceUserAccess.format(
            workspace_id,
            user_id,
        )
        organization_id: int | None = await self.cacher.get(key_organization, default=-1)
        if organization_id is None:
            return None

        if organization_id == -1:
            organization_id, user_access = await self._get_organization_id_and_user_access(
                user_id,
                workspace_id,
            )
            await self.cacher.set(key_organization, organization_id, ttl=300)
            if organization_id is not None:
                await self.cacher.set(
                    key_workspace_user_access,
                    user_access,
                    namespace=CacheConst.Organization.NamespaceOrganization.format(organization_id),
                    ttl=300,
                )
            return user_access

        namespace_organization = CacheConst.Organization.NamespaceOrganization.format(
            organization_id,
        )
        user_access: UserAccess | None | int = await self.cacher.get(
            key_workspace_user_access,
            namespace=namespace_organization,
            default=-1,
        )

        if user_access == -1:
            _, user_access = await self._get_organization_id_and_user_access(
                user_id,
                workspace_id,
            )
            await self.cacher.set(
                key_workspace_user_access,
                user_access,
                namespace=namespace_organization,
                ttl=300,
            )

        return user_access

    async def update_workspace(self, payload: UpdateWorkspacePayload) -> WorkspaceModel:
        workspace_orm = await self._get_orm_by_id(payload.workspace_id)
        workspace_orm.name = payload.name
        await self.session.commit()
        await self.session.refresh(workspace_orm)
        return DatabaseModelsConverter.workspace_orm_to_model(workspace_orm)

    async def delete_workspace(self, workspace_id: int) -> None:
        workspace_orm = await self._get_orm_by_id(workspace_id)
        workspace_orm.deleted = True
        organization_od = workspace_orm.organization_id
        await self.session.commit()
        await self._clear_cache_for_organization(organization_od)

