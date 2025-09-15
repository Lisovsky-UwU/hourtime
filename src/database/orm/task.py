import uuid

from sqlalchemy import UUID, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class TaskORM(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number: Mapped[int]
    name: Mapped[str]
    description: Mapped[str | None]
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    deleted: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        UniqueConstraint("workspace_id", "number", name="uix_workspace_number"),
    )

