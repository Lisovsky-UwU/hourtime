from pydantic import BaseModel


class ProjectModel(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: str | None
    color: str

