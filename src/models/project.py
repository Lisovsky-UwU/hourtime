from pydantic import BaseModel


class ProjectModel(BaseModel):
    id: int
    name: str
    description: str | None

