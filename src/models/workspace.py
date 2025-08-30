import uuid

from pydantic import BaseModel


class WorkspaceModel(BaseModel):
    id: int
    organization_id: uuid.UUID
    name: str

