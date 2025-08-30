from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ProjectORM(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str | None]
    workspace: Mapped[int] = mapped_column(ForeignKey("workspaces.id"))
    deleted: Mapped[bool] = mapped_column(default=False)

