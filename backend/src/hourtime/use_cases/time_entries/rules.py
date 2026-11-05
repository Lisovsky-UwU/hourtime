"""Rules shared by the time-entry use cases."""

from datetime import datetime, timedelta
from uuid import UUID

from hourtime.domain.entities import Project, Task
from hourtime.domain.errors import NotFound, ValidationError
from hourtime.interfaces.repositories import ProjectRepository, TagRepository, TaskRepository
from hourtime.use_cases.access import get_workspace_project, get_workspace_task

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
) -> Project | None:
    """Verify the project is in the entry's workspace and still usable."""
    if project_id is None:
        return None
    project = await get_workspace_project(projects, workspace_id, project_id)
    if project.is_archived:
        raise ValidationError("An archived project cannot be assigned")
    return project


async def resolve_task(
    tasks: TaskRepository,
    projects: ProjectRepository,
    workspace_id: UUID,
    *,
    task_id: UUID | None,
    project_id: UUID | None,
    current_task_id: UUID | None = None,
) -> Task | None:
    """Verify the task is in the entry's project and is still usable.

    Only a new assignment must be an active task of a live project: an entry
    keeps the task it already has when its other fields are edited.
    """
    if task_id is None:
        return None
    if project_id is None:
        raise ValidationError("A task cannot be assigned without a project")
    task, project = await get_workspace_task(tasks, projects, workspace_id, task_id)
    if task.project_id != project_id:
        raise ValidationError("The task belongs to another project")
    if task_id != current_task_id:
        if project.is_archived:
            raise ValidationError("Tasks of an archived project are read-only")
        if task.is_completed:
            raise ValidationError("A completed task cannot be assigned")
    return task


def resolve_billable(requested: bool | None, project: Project | None) -> bool:
    """An explicit choice wins; otherwise the entry follows its project's default."""
    if requested is not None:
        return requested
    return project.billable if project is not None else False


async def resolve_tags(tags: TagRepository, workspace_id: UUID, tag_ids: list[UUID]) -> list[UUID]:
    """Verify every tag is in the entry's workspace; repeated ids count once."""
    wanted = set(tag_ids)
    if not wanted:
        return []
    found = await tags.get_many(list(wanted))
    if len(found) != len(wanted) or any(tag.workspace_id != workspace_id for tag in found):
        raise NotFound("Tag not found")
    return sorted(wanted)
