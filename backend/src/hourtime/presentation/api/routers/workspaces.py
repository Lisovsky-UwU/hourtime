from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from hourtime.presentation.api.deps import (
    CurrentMemberDep,
    CurrentUserDep,
    get_create_invite,
    get_get_workspace,
    get_list_invites,
    get_list_members,
    get_list_workspaces,
    get_remove_member,
    get_revoke_invite,
    get_update_member,
    get_update_workspace,
)
from hourtime.presentation.api.schemas.workspaces import (
    CreateInviteRequest,
    InviteResponse,
    IssuedInviteResponse,
    MemberResponse,
    MemberWorkspaceResponse,
    UpdateMemberRequest,
    UpdateWorkspaceRequest,
)
from hourtime.use_cases.dto import MemberWorkspace, UpdateWorkspaceInput
from hourtime.use_cases.workspaces import (
    CreateInvite,
    GetWorkspace,
    ListInvites,
    ListMembers,
    ListWorkspaces,
    RemoveMember,
    RevokeInvite,
    UpdateMember,
    UpdateWorkspace,
)

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


@router.get("/{workspace_id}/members", response_model=list[MemberResponse])
async def list_members(
    current: CurrentMemberDep,
    use_case: Annotated[ListMembers, Depends(get_list_members)],
) -> list[MemberResponse]:
    return [MemberResponse.of(account) for account in await use_case.execute(current.workspace_id)]


@router.patch("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_member(
    user_id: UUID,
    body: UpdateMemberRequest,
    current: CurrentMemberDep,
    use_case: Annotated[UpdateMember, Depends(get_update_member)],
) -> Response:
    await use_case.execute(current.workspace_id, user_id, body.role, role=current.member.role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    user_id: UUID,
    current: CurrentMemberDep,
    use_case: Annotated[RemoveMember, Depends(get_remove_member)],
) -> Response:
    """Removes someone, or leaves the workspace when `user_id` is the caller."""
    await use_case.execute(current.workspace_id, user_id, caller=current.member)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{workspace_id}/invites", response_model=list[InviteResponse])
async def list_invites(
    current: CurrentMemberDep,
    use_case: Annotated[ListInvites, Depends(get_list_invites)],
) -> list[InviteResponse]:
    found = await use_case.execute(current.workspace_id, role=current.member.role)
    return [InviteResponse.of(invite) for invite in found]


@router.post(
    "/{workspace_id}/invites",
    response_model=IssuedInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invite(
    body: CreateInviteRequest,
    current: CurrentMemberDep,
    use_case: Annotated[CreateInvite, Depends(get_create_invite)],
) -> IssuedInviteResponse:
    issued = await use_case.execute(
        current.workspace_id, current.user.id, role=current.member.role, invited_role=body.role
    )
    return IssuedInviteResponse(**InviteResponse.of(issued.invite).model_dump(), token=issued.token)


@router.delete("/{workspace_id}/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invite(
    invite_id: UUID,
    current: CurrentMemberDep,
    use_case: Annotated[RevokeInvite, Depends(get_revoke_invite)],
) -> Response:
    await use_case.execute(current.workspace_id, invite_id, role=current.member.role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
