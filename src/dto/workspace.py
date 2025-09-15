from pydantic import BaseModel

from src.models.common import UserAccess


class CreateWorkspacePayload(BaseModel):
    organization_id: int
    name: str


class UpdateWorkspacePayload(BaseModel):
    workspace_id: int
    name: str


class WorkspaceSubElement(BaseModel):
    id: int
    name: str


class WorkspaceListWithAccess(BaseModel):
    access: UserAccess
    workspaces: list[WorkspaceSubElement]

