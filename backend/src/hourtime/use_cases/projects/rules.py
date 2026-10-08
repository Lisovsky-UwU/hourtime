"""Rules shared by the project use cases."""

from uuid import UUID

from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import ClientRepository
from hourtime.use_cases.access import get_workspace_client


async def resolve_client(
    clients: ClientRepository, workspace_id: UUID, client_id: UUID | None
) -> UUID | None:
    """Verify the client is in the project's workspace and still usable."""
    if client_id is None:
        return None
    client = await get_workspace_client(clients, workspace_id, client_id)
    if client.is_archived:
        raise ValidationError("An archived client cannot be assigned")
    return client.id
