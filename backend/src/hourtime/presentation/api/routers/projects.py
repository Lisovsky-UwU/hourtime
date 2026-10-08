from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from hourtime.presentation.api.deps import (
    CurrentUserDep,
    get_create_project,
    get_delete_project,
    get_list_projects,
    get_update_project,
)
from hourtime.presentation.api.schemas.projects import (
    CreateProjectRequest,
    ProjectResponse,
    UpdateProjectRequest,
)
from hourtime.use_cases.dto import CreateProjectInput, UpdateProjectInput
from hourtime.use_cases.projects import CreateProject, DeleteProject, ListProjects, UpdateProject

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current: CurrentUserDep,
    use_case: Annotated[ListProjects, Depends(get_list_projects)],
    include_archived: Annotated[bool, Query()] = False,
) -> list[ProjectResponse]:
    projects = await use_case.execute(current.workspace_id, include_archived=include_archived)
    return [ProjectResponse.of(project) for project in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: CreateProjectRequest,
    current: CurrentUserDep,
    use_case: Annotated[CreateProject, Depends(get_create_project)],
) -> ProjectResponse:
    project = await use_case.execute(
        CreateProjectInput(
            workspace_id=current.workspace_id,
            name=body.name,
            color=body.color,
            client_id=body.client_id,
            billable=body.billable,
            hourly_rate=body.hourly_rate,
        )
    )
    return ProjectResponse.of(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    body: UpdateProjectRequest,
    current: CurrentUserDep,
    use_case: Annotated[UpdateProject, Depends(get_update_project)],
) -> ProjectResponse:
    # `exclude_unset` is what lets the use case tell "not sent" from "set to null".
    project = await use_case.execute(
        UpdateProjectInput(
            workspace_id=current.workspace_id,
            project_id=project_id,
            **body.model_dump(exclude_unset=True),
        )
    )
    return ProjectResponse.of(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current: CurrentUserDep,
    use_case: Annotated[DeleteProject, Depends(get_delete_project)],
) -> Response:
    await use_case.execute(current.workspace_id, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
