from pydantic import BaseModel


class CreateWorkspacePayload(BaseModel):
    organization_id: int
    name: str


class WorkspaceSubElement(BaseModel):
    id: int
    name: str

