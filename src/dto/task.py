from pydantic import BaseModel


class CreateTaskPayload(BaseModel):
    name: str
    description: str | None
    project_id: int

