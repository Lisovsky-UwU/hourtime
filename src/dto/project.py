from pydantic import BaseModel


class CreateProjectPayload(BaseModel):
    workspace_id: int
    name: str
    description: str | None
    color: str


class UpdateProjectPayload(BaseModel):
    project_id: int
    name: str
    description: str | None
    color: str

