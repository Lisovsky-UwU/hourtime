from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class WorkspaceORM(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    deleted: Mapped[bool] = mapped_column(default=False)

    organization: Mapped["OrganizationORM"] = relationship(back_populates="workspaces")


from src.database.orm.organization import OrganizationORM

