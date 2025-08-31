from pydantic import BaseModel

from src.models.organization import UserAccess


class CreateOrganizationPayload(BaseModel):
    name: str


class UpdateOrganizationPayload(BaseModel):
    organization_id: int
    name: str


class AddUserToOrganizationElement(BaseModel):
    user_id: int
    access: UserAccess


class AddUserToOrganizationPayload(BaseModel):
    organization_id: int
    users: list[AddUserToOrganizationElement]

