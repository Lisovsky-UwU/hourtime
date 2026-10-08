from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from hourtime.presentation.api.deps import (
    CurrentUserDep,
    get_create_tag,
    get_delete_tag,
    get_list_tags,
    get_update_tag,
)
from hourtime.presentation.api.schemas.tags import CreateTagRequest, TagResponse, UpdateTagRequest
from hourtime.use_cases.dto import CreateTagInput, UpdateTagInput
from hourtime.use_cases.tags import CreateTag, DeleteTag, ListTags, UpdateTag

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current: CurrentUserDep,
    use_case: Annotated[ListTags, Depends(get_list_tags)],
) -> list[TagResponse]:
    tags = await use_case.execute(current.workspace_id)
    return [TagResponse.of(tag) for tag in tags]


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    body: CreateTagRequest,
    current: CurrentUserDep,
    use_case: Annotated[CreateTag, Depends(get_create_tag)],
) -> TagResponse:
    tag = await use_case.execute(CreateTagInput(workspace_id=current.workspace_id, name=body.name))
    return TagResponse.of(tag)


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: UUID,
    body: UpdateTagRequest,
    current: CurrentUserDep,
    use_case: Annotated[UpdateTag, Depends(get_update_tag)],
) -> TagResponse:
    tag = await use_case.execute(
        UpdateTagInput(workspace_id=current.workspace_id, tag_id=tag_id, name=body.name)
    )
    return TagResponse.of(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    current: CurrentUserDep,
    use_case: Annotated[DeleteTag, Depends(get_delete_tag)],
) -> Response:
    await use_case.execute(current.workspace_id, tag_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
