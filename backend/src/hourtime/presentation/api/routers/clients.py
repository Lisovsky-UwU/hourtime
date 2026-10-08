from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from hourtime.presentation.api.deps import (
    CurrentUserDep,
    get_create_client,
    get_delete_client,
    get_list_clients,
    get_update_client,
)
from hourtime.presentation.api.schemas.clients import (
    ClientResponse,
    CreateClientRequest,
    UpdateClientRequest,
)
from hourtime.use_cases.clients import CreateClient, DeleteClient, ListClients, UpdateClient
from hourtime.use_cases.dto import CreateClientInput, UpdateClientInput

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientResponse])
async def list_clients(
    current: CurrentUserDep,
    use_case: Annotated[ListClients, Depends(get_list_clients)],
    include_archived: Annotated[bool, Query()] = False,
) -> list[ClientResponse]:
    clients = await use_case.execute(current.workspace_id, include_archived=include_archived)
    return [ClientResponse.of(client) for client in clients]


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: CreateClientRequest,
    current: CurrentUserDep,
    use_case: Annotated[CreateClient, Depends(get_create_client)],
) -> ClientResponse:
    client = await use_case.execute(
        CreateClientInput(workspace_id=current.workspace_id, name=body.name)
    )
    return ClientResponse.of(client)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    body: UpdateClientRequest,
    current: CurrentUserDep,
    use_case: Annotated[UpdateClient, Depends(get_update_client)],
) -> ClientResponse:
    client = await use_case.execute(
        UpdateClientInput(
            workspace_id=current.workspace_id,
            client_id=client_id,
            **body.model_dump(exclude_unset=True),
        )
    )
    return ClientResponse.of(client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    current: CurrentUserDep,
    use_case: Annotated[DeleteClient, Depends(get_delete_client)],
) -> Response:
    await use_case.execute(current.workspace_id, client_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
