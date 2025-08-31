from pydantic import BaseModel


class CreateOrganizationByUserRequest(BaseModel):
    name: str


class UpdateOrganizationRequest(BaseModel):
    organization_id: int
    name: str

