from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    workspace_id: int
    name: str
    description: str | None = None


class UpdateProjectRequest(BaseModel):
    project_id: int
    name: str
    description: str | None = None

