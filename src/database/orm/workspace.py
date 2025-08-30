from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class WorkspaceORM(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    organization: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    deleted: Mapped[bool] = mapped_column(default=False)

