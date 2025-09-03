from pydantic import BaseModel


class CreateWorkspaceByUserRequest(BaseModel):
    name: str
    organization_id: int

