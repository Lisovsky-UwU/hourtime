import uuid

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.models.organization import UserAccess

from . import Base


class LinkUserOrganizationORM(Base):
    __tablename__ = "links_user_organization"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    access: Mapped[UserAccess]

