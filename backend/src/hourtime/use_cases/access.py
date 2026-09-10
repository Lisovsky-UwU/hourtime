"""Ownership checks shared by the use cases.

Everything belongs to exactly one user, and a resource owned by somebody else
is reported as missing rather than forbidden — a 403 would confirm that the id
exists.
"""

from uuid import UUID

from hourtime.domain.entities import Project, TimeEntry
from hourtime.domain.errors import NotFound
from hourtime.interfaces.repositories import ProjectRepository, TimeEntryRepository


async def get_owned_project(
    projects: ProjectRepository, user_id: UUID, project_id: UUID
) -> Project:
    project = await projects.get_by_id(project_id)
    if project is None or project.user_id != user_id:
        raise NotFound("Project not found")
    return project


async def get_owned_time_entry(
    entries: TimeEntryRepository, user_id: UUID, entry_id: UUID
) -> TimeEntry:
    entry = await entries.get_by_id(entry_id)
    if entry is None or entry.user_id != user_id:
        raise NotFound("Time entry not found")
    return entry
