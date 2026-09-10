"""Rules shared by the time-entry use cases."""

from datetime import datetime, timedelta
from uuid import UUID

from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import ProjectRepository
from hourtime.use_cases.access import get_owned_project

# Browsers stop timers against their own clock, which drifts from the server's.
# Anything inside this window is treated as "now" rather than rejected.
FUTURE_TOLERANCE = timedelta(seconds=60)

# Validation messages reach the user verbatim, so they name what the form calls
# these fields rather than what the API does.
START_TIME = "start time"
END_TIME = "end time"


def reject_future(value: datetime, now: datetime, field: str) -> None:
    if value > now + FUTURE_TOLERANCE:
        raise ValidationError(f"The {field} cannot be in the future")


async def resolve_project(
    projects: ProjectRepository, user_id: UUID, project_id: UUID | None
) -> UUID | None:
    """Verify the project is the caller's and still usable."""
    if project_id is None:
        return None
    project = await get_owned_project(projects, user_id, project_id)
    if project.is_archived:
        raise ValidationError("An archived project cannot be assigned")
    return project.id
