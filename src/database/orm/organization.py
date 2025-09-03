from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class OrganizationORM(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    deleted: Mapped[bool] = mapped_column(default=False)

    users: Mapped[list["UserORM"]] = relationship(
        secondary="links_user_organization",
        back_populates="organizations",
    )
    workspaces: Mapped[list["WorkspaceORM"]] = relationship(back_populates="organization")


from .user import UserORM
from .workspace import WorkspaceORM

