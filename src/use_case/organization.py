import abc

from src.dto.organization import (
    AddUserToOrganizationPayload,
    CreateOrganizationPayload,
    UpdateOrganizationPayload,
)
from src.models.organization import OrganizationModel


class OrganizationUseCase(abc.ABC):

    @abc.abstractmethod
    async def create_organization(self, payload: CreateOrganizationPayload) -> OrganizationModel:
        ...

    @abc.abstractmethod
    async def add_users_to_organization(
        self,
        payload: AddUserToOrganizationPayload,
    ) -> OrganizationModel:
        ...

    @abc.abstractmethod
    async def update_organization(self, payload: UpdateOrganizationPayload) -> OrganizationModel:
        ...

    @abc.abstractmethod
    async def delete_organization(self, organization_id: int) -> None:
        ...

