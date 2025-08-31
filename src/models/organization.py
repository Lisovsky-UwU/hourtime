from pydantic import BaseModel

from .common import UserAccess


class OrganizationModel(BaseModel):
    id: int
    name: str

class UserOrganizationModel(BaseModel):
    organization_id: int
    organization_name: str
    access: UserAccess

