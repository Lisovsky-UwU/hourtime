"""Rules shared by the time-entry use cases."""

from datetime import datetime, timedelta
from uuid import UUID

from hourtime.domain.errors import NotFound, ValidationError
from hourtime.interfaces.repositories import ProjectRepository, TagRepository
from hourtime.use_cases.access import get_workspace_project

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
    projects: ProjectRepository, workspace_id: UUID, project_id: UUID | None
) -> UUID | None:
    """Verify the project is in the entry's workspace and still usable."""
    if project_id is None:
        return None
    project = await get_workspace_project(projects, workspace_id, project_id)
    if project.is_archived:
        raise ValidationError("An archived project cannot be assigned")
    return project.id


async def resolve_tags(tags: TagRepository, workspace_id: UUID, tag_ids: list[UUID]) -> list[UUID]:
    """Verify every tag is in the entry's workspace; repeated ids count once."""
    wanted = set(tag_ids)
    if not wanted:
        return []
    found = await tags.get_many(list(wanted))
    if len(found) != len(wanted) or any(tag.workspace_id != workspace_id for tag in found):
        raise NotFound("Tag not found")
    return sorted(wanted)
