from pydantic import BaseModel


class CreateWorkspaceByUserRequest(BaseModel):
    name: str
    organization_id: int

class UpdateWorkspaceByUserRequest(BaseModel):
    workspace_id: int
    name: str

