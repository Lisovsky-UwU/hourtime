from pydantic import BaseModel


class WorkspaceModel(BaseModel):
    id: int
    organization_id: int
    name: str

