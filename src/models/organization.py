from enum import StrEnum

from pydantic import BaseModel


class UserAccess(StrEnum):
    OWNER = "Owner"
    FULL = "Full Access"
    PARTIAL = "Partial Access"


class UserOrganizationSettingsModel(BaseModel):
    user_id: int
    access: UserAccess


class OrganizationModel(BaseModel):
    id: int
    name: str

