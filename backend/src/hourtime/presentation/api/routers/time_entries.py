from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from hourtime.presentation.api.deps import (
    CurrentUserDep,
    get_create_time_entry,
    get_delete_time_entry,
    get_list_time_entries,
    get_running_timer,
    get_start_timer,
    get_stop_timer,
    get_suggest_time_entries,
    get_update_time_entry,
)
from hourtime.presentation.api.schemas.time_entries import (
    CreateTimeEntryRequest,
    StartTimerRequest,
    StopTimerRequest,
    TimeEntryPageResponse,
    TimeEntryResponse,
    TimeEntrySuggestionResponse,
    UpdateTimeEntryRequest,
)
from hourtime.use_cases.dto import (
    CreateTimeEntryInput,
    ListTimeEntriesInput,
    StartTimerInput,
    StopTimerInput,
    SuggestTimeEntriesInput,
    UpdateTimeEntryInput,
)
from hourtime.use_cases.time_entries import (
    CreateTimeEntry,
    DeleteTimeEntry,
    GetRunningTimer,
    ListTimeEntries,
    StartTimer,
    StopTimer,
    SuggestTimeEntries,
    UpdateTimeEntry,
)

router = APIRouter(prefix="/time-entries", tags=["time-entries"])


@router.get("", response_model=TimeEntryPageResponse)
async def list_time_entries(
    current: CurrentUserDep,
    use_case: Annotated[ListTimeEntries, Depends(get_list_time_entries)],
    started_from: Annotated[datetime | None, Query()] = None,
    started_to: Annotated[datetime | None, Query()] = None,
    project_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TimeEntryPageResponse:
    page = await use_case.execute(
        ListTimeEntriesInput(
            user_id=current.user.id,
            workspace_id=current.workspace_id,
            started_from=started_from,
            started_to=started_to,
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
    )
    return TimeEntryPageResponse.of(page)


@router.get("/suggestions", response_model=list[TimeEntrySuggestionResponse])
async def suggest_time_entries(
    current: CurrentUserDep,
    use_case: Annotated[SuggestTimeEntries, Depends(get_suggest_time_entries)],
    q: Annotated[str, Query(max_length=200)] = "",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[TimeEntrySuggestionResponse]:
    found = await use_case.execute(
        SuggestTimeEntriesInput(
            user_id=current.user.id, workspace_id=current.workspace_id, query=q, limit=limit
        )
    )
    return [TimeEntrySuggestionResponse.of(suggestion) for suggestion in found]


@router.get("/current", response_model=TimeEntryResponse | None)
async def current_timer(
    current: CurrentUserDep,
    use_case: Annotated[GetRunningTimer, Depends(get_running_timer)],
) -> TimeEntryResponse | None:
    entry = await use_case.execute(current.user.id)
    return TimeEntryResponse.of(entry) if entry else None


@router.post("/start", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
async def start_timer(
    body: StartTimerRequest,
    current: CurrentUserDep,
    use_case: Annotated[StartTimer, Depends(get_start_timer)],
) -> TimeEntryResponse:
    entry = await use_case.execute(
        StartTimerInput(
            user_id=current.user.id,
            workspace_id=current.workspace_id,
            project_id=body.project_id,
            description=body.description,
            started_at=body.started_at,
        )
    )
    return TimeEntryResponse.of(entry)


@router.post("/{entry_id}/stop", response_model=TimeEntryResponse)
async def stop_timer(
    entry_id: UUID,
    body: StopTimerRequest,
    current: CurrentUserDep,
    use_case: Annotated[StopTimer, Depends(get_stop_timer)],
) -> TimeEntryResponse:
    entry = await use_case.execute(
        StopTimerInput(
            user_id=current.user.id,
            workspace_id=current.workspace_id,
            entry_id=entry_id,
            stopped_at=body.stopped_at,
        )
    )
    return TimeEntryResponse.of(entry)


@router.post("", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_time_entry(
    body: CreateTimeEntryRequest,
    current: CurrentUserDep,
    use_case: Annotated[CreateTimeEntry, Depends(get_create_time_entry)],
) -> TimeEntryResponse:
    entry = await use_case.execute(
        CreateTimeEntryInput(
            user_id=current.user.id,
            workspace_id=current.workspace_id,
            project_id=body.project_id,
            description=body.description,
            started_at=body.started_at,
            stopped_at=body.stopped_at,
        )
    )
    return TimeEntryResponse.of(entry)


@router.patch("/{entry_id}", response_model=TimeEntryResponse)
async def update_time_entry(
    entry_id: UUID,
    body: UpdateTimeEntryRequest,
    current: CurrentUserDep,
    use_case: Annotated[UpdateTimeEntry, Depends(get_update_time_entry)],
) -> TimeEntryResponse:
    entry = await use_case.execute(
        UpdateTimeEntryInput(
            user_id=current.user.id,
            workspace_id=current.workspace_id,
            entry_id=entry_id,
            **body.model_dump(exclude_unset=True),
        )
    )
    return TimeEntryResponse.of(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_entry(
    entry_id: UUID,
    current: CurrentUserDep,
    use_case: Annotated[DeleteTimeEntry, Depends(get_delete_time_entry)],
) -> Response:
    await use_case.execute(current.user.id, current.workspace_id, entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
