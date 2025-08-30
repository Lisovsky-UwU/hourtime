import uuid
from datetime import date, time

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class TimeEntryORM(Base):
    __tablename__ = "time_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    comment: Mapped[str | None]
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tasks.id"))
    start_date: Mapped[date]
    start_time: Mapped[time]
    end_date: Mapped[date | None]
    end_time: Mapped[time | None]
    deleted: Mapped[bool] = mapped_column(default=False)

