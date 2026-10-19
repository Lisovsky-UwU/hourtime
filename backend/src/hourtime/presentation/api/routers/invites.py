from typing import Annotated

from fastapi import APIRouter, Depends

from hourtime.presentation.api.deps import CurrentUserDep, get_accept_invite, get_preview_invite
from hourtime.presentation.api.schemas.workspaces import (
    InvitePreviewResponse,
    InviteTokenRequest,
    MemberWorkspaceResponse,
)
from hourtime.use_cases.workspaces import AcceptInvite, PreviewInvite

router = APIRouter(prefix="/invites", tags=["workspaces"])


@router.post("/preview", response_model=InvitePreviewResponse)
async def preview_invite(
    body: InviteTokenRequest,
    use_case: Annotated[PreviewInvite, Depends(get_preview_invite)],
) -> InvitePreviewResponse:
    """Public: the invite page shows it before the visitor signs in or registers."""
    preview = await use_case.execute(body.token)
    return InvitePreviewResponse(**preview.model_dump())


@router.post("/accept", response_model=MemberWorkspaceResponse)
async def accept_invite(
    body: InviteTokenRequest,
    current: CurrentUserDep,
    use_case: Annotated[AcceptInvite, Depends(get_accept_invite)],
) -> MemberWorkspaceResponse:
    return MemberWorkspaceResponse.of_member(await use_case.execute(current.user, body.token))
