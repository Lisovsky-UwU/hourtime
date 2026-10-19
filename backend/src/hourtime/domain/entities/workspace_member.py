from typing import Literal
from uuid import UUID

from hourtime.domain.entities.base import Entity, UtcDatetime

MemberRole = Literal["admin", "member"]


class WorkspaceMember(Entity):
    """A user's access to a workspace. The owner is always an admin."""

    workspace_id: UUID
    user_id: UUID
    role: MemberRole
    created_at: UtcDatetime
