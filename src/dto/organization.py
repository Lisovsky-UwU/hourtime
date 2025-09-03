from pydantic import BaseModel

from src.dto.workspace import WorkspaceSubElement
from src.models.common import UserAccess


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


class UserOrganizationWithWorkspaces(BaseModel):
    organization_id: int
    name: str
    access: UserAccess
    workspaces: list[WorkspaceSubElement]

