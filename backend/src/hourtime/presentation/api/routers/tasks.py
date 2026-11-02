from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from hourtime.domain.errors import ValidationError
from hourtime.presentation.api.deps import (
    CurrentMemberDep,
    get_complete_task,
    get_create_task,
    get_delete_task,
    get_list_tasks,
    get_reopen_task,
    get_update_task,
)
from hourtime.presentation.api.schemas.tasks import (
    CreateTaskRequest,
    TaskResponse,
    UpdateTaskRequest,
)
from hourtime.use_cases.dto import CreateTaskInput, UpdateTaskInput
from hourtime.use_cases.tasks import (
    CompleteTask,
    CreateTask,
    DeleteTask,
    ListTasks,
    ReopenTask,
    UpdateTask,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    current: CurrentMemberDep,
    use_case: Annotated[ListTasks, Depends(get_list_tasks)],
    project_id: Annotated[UUID | None, Query()] = None,
    include_completed: Annotated[bool, Query()] = False,
) -> list[TaskResponse]:
    tasks = await use_case.execute(
        current.workspace_id, project_id=project_id, include_completed=include_completed
    )
    return [TaskResponse.of(task) for task in tasks]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: CreateTaskRequest,
    current: CurrentMemberDep,
    use_case: Annotated[CreateTask, Depends(get_create_task)],
) -> TaskResponse:
    task = await use_case.execute(
        CreateTaskInput(
            workspace_id=current.workspace_id,
            project_id=body.project_id,
            name=body.name,
            estimated_seconds=body.estimated_seconds,
        )
    )
    return TaskResponse.of(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    body: UpdateTaskRequest,
    current: CurrentMemberDep,
    update: Annotated[UpdateTask, Depends(get_update_task)],
    complete: Annotated[CompleteTask, Depends(get_complete_task)],
    reopen: Annotated[ReopenTask, Depends(get_reopen_task)],
) -> TaskResponse:
    if body.completed is not None:
        if body.name is not None or "estimated_seconds" in body.model_fields_set:
            raise ValidationError("Change the completion state separately from other fields")
        use_case = complete if body.completed else reopen
        task = await use_case.execute(current.workspace_id, task_id, role=current.member.role)
        return TaskResponse.of(task)
    task = await update.execute(
        UpdateTaskInput(
            workspace_id=current.workspace_id,
            role=current.member.role,
            task_id=task_id,
            **body.model_dump(exclude_unset=True),
        )
    )
    return TaskResponse.of(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current: CurrentMemberDep,
    use_case: Annotated[DeleteTask, Depends(get_delete_task)],
) -> Response:
    await use_case.execute(current.workspace_id, task_id, role=current.member.role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
