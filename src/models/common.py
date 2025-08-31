from enum import StrEnum


class UserAccess(StrEnum):
    OWNER = "Owner"
    FULL = "Full Access"
    PARTIAL = "Partial Access"

