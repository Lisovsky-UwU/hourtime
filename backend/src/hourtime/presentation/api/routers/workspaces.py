from typing import Annotated

from fastapi import APIRouter, Depends

from hourtime.presentation.api.deps import (
    CurrentUserDep,
    get_get_workspace,
    get_update_workspace,
)
from hourtime.presentation.api.schemas.workspaces import (
    UpdateWorkspaceRequest,
    WorkspaceResponse,
)
from hourtime.use_cases.dto import UpdateWorkspaceInput
from hourtime.use_cases.workspaces import GetWorkspace, UpdateWorkspace

# "current" is the caller's default workspace; ids in the path come with shared workspaces.
router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/current", response_model=WorkspaceResponse)
async def get_current_workspace(
    current: CurrentUserDep,
    use_case: Annotated[GetWorkspace, Depends(get_get_workspace)],
) -> WorkspaceResponse:
    return WorkspaceResponse.of(await use_case.execute(current.workspace_id))


@router.patch("/current", response_model=WorkspaceResponse)
async def update_current_workspace(
    body: UpdateWorkspaceRequest,
    current: CurrentUserDep,
    use_case: Annotated[UpdateWorkspace, Depends(get_update_workspace)],
) -> WorkspaceResponse:
    workspace = await use_case.execute(
        UpdateWorkspaceInput(
            workspace_id=current.workspace_id, **body.model_dump(exclude_unset=True)
        )
    )
    return WorkspaceResponse.of(workspace)
