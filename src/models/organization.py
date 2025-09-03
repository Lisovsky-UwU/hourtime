from pydantic import BaseModel


class OrganizationModel(BaseModel):
    id: int
    name: str

