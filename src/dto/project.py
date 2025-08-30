from pydantic import BaseModel


class CreateProjectPayload(BaseModel):
    name: str
    description: str | None

