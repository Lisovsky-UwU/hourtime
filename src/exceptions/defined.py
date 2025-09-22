from src.exceptions.types import AccessError, ValidationError

ORGANIZATION_ACCESS_ERROR = AccessError(
    21,
    "Access denied",
    "You don't have enough rights to access organization.",
)

TIME_ENTRY_TIMES_ERROR = ValidationError(
    62,
    "Times error",
    "The end time cannot be earlier than the start time",
)

