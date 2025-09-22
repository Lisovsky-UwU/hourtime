import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from src.api.depends import check_user_token, service_time_entry_depends
from src.api.handlers import LoggingRoute
from src.dto.api.common import ResultResponse
from src.dto.api.time_entry import (
    TimeENtryCreateRequest,
    TimeEntryStartRequest,
    TimeEntryUpdateRequest,
)
from src.dto.time_entry import (
    CreateTimeEntryPayload,
    TimeEntryForUser,
    TimeEntryGetFilterData,
    UpdateTimeEntryPayload,
)
from src.models.time_entery import TimeEntryModel
from src.models.user import UserModel
from src.service.time_entry import TimeEntryService

time_entry_route = APIRouter(prefix="/time_entry", route_class=LoggingRoute)


@time_entry_route.post("/start")
async def start_time_for_user(
    request_body: TimeEntryStartRequest,
    user_model: UserModel = Depends(check_user_token),
    time_entry_service: TimeEntryService = Depends(service_time_entry_depends),
) -> TimeEntryModel:
    return await time_entry_service.create_entry_by_user(
        CreateTimeEntryPayload(
            user_id=user_model.id,
            comment=request_body.comment,
            workspace_id=request_body.workspace_id,
            project_id=request_body.project_id,
            task_id=request_body.task_id,
            start_date=request_body.start_date or datetime.now().date(),
            start_time=request_body.start_time or datetime.now().time(),
            end_date=None,
            end_time=None,
        ),
    )

@time_entry_route.post("/create")
async def create_time_by_user(
    request_body: TimeENtryCreateRequest,
    user_model: UserModel = Depends(check_user_token),
    time_entry_service: TimeEntryService = Depends(service_time_entry_depends),
) -> TimeEntryModel:
    return await time_entry_service.create_entry_by_user(
        CreateTimeEntryPayload(
            user_id=user_model.id,
            comment=request_body.comment,
            workspace_id=request_body.workspace_id,
            project_id=request_body.project_id,
            task_id=request_body.task_id,
            start_date=request_body.start_date,
            start_time=request_body.start_time,
            end_date=request_body.end_date,
            end_time=request_body.end_time,
        ),
    )

@time_entry_route.get("/get_my")
async def get_time_entries_by_user(
    workspace_id: int | None = None,
    date_start: str = Query(description="Format: YYYY-MM-DD"),
    date_end: str = Query(description="Format: YYYY-MM-DD"),
    user_model: UserModel = Depends(check_user_token),
    time_entry_service: TimeEntryService = Depends(service_time_entry_depends),
) -> list[TimeEntryForUser]:
    return await time_entry_service.get_for_user(
        TimeEntryGetFilterData(
            user_id=user_model.id,
            workspace_id=workspace_id,
            range_date_start=datetime.strptime(date_start, "%Y-%m-%d"),
            range_date_end=datetime.strptime(date_end, "%Y-%m-%d"),
        ),
    )

@time_entry_route.put("/update")
async def update_time_entry_by_user(
    request_body: TimeEntryUpdateRequest,
    user_model: UserModel = Depends(check_user_token),
    time_entry_service: TimeEntryService = Depends(service_time_entry_depends),
) -> TimeEntryModel:
    return await time_entry_service.update_entry_by_user(
        user_model.id,
        UpdateTimeEntryPayload(
            time_entry_id=request_body.time_entry_id,
            comment=request_body.comment,
            project_id=request_body.project_id,
            task_id=request_body.task_id,
            start_date=request_body.start_date,
            start_time=request_body.start_time,
            end_date=request_body.end_date,
            end_time=request_body.end_time,
        ),
    )

@time_entry_route.delete("/delete")
async def delete_time_entry_by_user(
    time_entry_id: uuid.UUID,
    user_model: UserModel = Depends(check_user_token),
    time_entry_service: TimeEntryService = Depends(service_time_entry_depends),
) -> ResultResponse:
    await time_entry_service.delete_entry_by_user(user_model.id, time_entry_id)
    return ResultResponse()

