from typing import Annotated

from fastapi import APIRouter, Depends

from hourtime.presentation.api.deps import (
    CurrentMemberDep,
    CurrentUserDep,
    get_get_workspace,
    get_list_workspaces,
    get_update_workspace,
)
from hourtime.presentation.api.schemas.workspaces import (
    MemberWorkspaceResponse,
    UpdateWorkspaceRequest,
)
from hourtime.use_cases.dto import MemberWorkspace, UpdateWorkspaceInput
from hourtime.use_cases.workspaces import GetWorkspace, ListWorkspaces, UpdateWorkspace

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[MemberWorkspaceResponse])
async def list_workspaces(
    current: CurrentUserDep,
    use_case: Annotated[ListWorkspaces, Depends(get_list_workspaces)],
) -> list[MemberWorkspaceResponse]:
    found = await use_case.execute(current.user.id)
    return [MemberWorkspaceResponse.of_member(item) for item in found]


@router.get("/{workspace_id}", response_model=MemberWorkspaceResponse)
async def get_workspace(
    current: CurrentMemberDep,
    use_case: Annotated[GetWorkspace, Depends(get_get_workspace)],
) -> MemberWorkspaceResponse:
    workspace = await use_case.execute(current.workspace_id)
    return MemberWorkspaceResponse.of_member(
        MemberWorkspace(workspace=workspace, role=current.member.role)
    )


@router.patch("/{workspace_id}", response_model=MemberWorkspaceResponse)
async def update_workspace(
    body: UpdateWorkspaceRequest,
    current: CurrentMemberDep,
    use_case: Annotated[UpdateWorkspace, Depends(get_update_workspace)],
) -> MemberWorkspaceResponse:
    workspace = await use_case.execute(
        UpdateWorkspaceInput(
            workspace_id=current.workspace_id,
            role=current.member.role,
            **body.model_dump(exclude_unset=True),
        )
    )
    return MemberWorkspaceResponse.of_member(
        MemberWorkspace(workspace=workspace, role=current.member.role)
    )
