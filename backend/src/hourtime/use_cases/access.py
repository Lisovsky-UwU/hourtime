"""Ownership checks shared by the use cases.

Clients, projects and tags belong to a workspace, time entries to a workspace
and the user who tracked them. A resource from somewhere else is reported as
missing rather than forbidden - a 403 would confirm that the id exists.

The workspace id comes from the URL, so every request into a workspace starts
with `require_member`; the checks below then trust it.
"""

from uuid import UUID

from hourtime.domain.entities import Client, Project, Tag, TimeEntry, WorkspaceMember
from hourtime.domain.errors import NotFound
from hourtime.interfaces.repositories import (
    ClientRepository,
    ProjectRepository,
    TagRepository,
    TimeEntryRepository,
    WorkspaceMemberRepository,
)


async def require_member(
    members: WorkspaceMemberRepository, workspace_id: UUID, user_id: UUID
) -> WorkspaceMember:
    member = await members.get(workspace_id, user_id)
    if member is None:
        raise NotFound("Workspace not found")
    return member


async def get_workspace_client(
    clients: ClientRepository, workspace_id: UUID, client_id: UUID
) -> Client:
    client = await clients.get_by_id(client_id)
    if client is None or client.workspace_id != workspace_id:
        raise NotFound("Client not found")
    return client


async def get_workspace_project(
    projects: ProjectRepository, workspace_id: UUID, project_id: UUID
) -> Project:
    project = await projects.get_by_id(project_id)
    if project is None or project.workspace_id != workspace_id:
        raise NotFound("Project not found")
    return project


async def get_workspace_tag(tags: TagRepository, workspace_id: UUID, tag_id: UUID) -> Tag:
    tag = await tags.get_by_id(tag_id)
    if tag is None or tag.workspace_id != workspace_id:
        raise NotFound("Tag not found")
    return tag


async def get_owned_time_entry(
    entries: TimeEntryRepository, user_id: UUID, workspace_id: UUID, entry_id: UUID
) -> TimeEntry:
    entry = await entries.get_by_id(entry_id)
    if entry is None or entry.user_id != user_id or entry.workspace_id != workspace_id:
        raise NotFound("Time entry not found")
    return entry
