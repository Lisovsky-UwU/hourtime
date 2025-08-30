from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    display_name: Mapped[str]
    pass_hash: Mapped[str]
    deleted: Mapped[bool] = mapped_column(default=False)

    organizations: Mapped[list["OrganizationORM"]] = relationship(
        secondary="links_user_organization",
        back_populates="users",
    )

    tokens: Mapped[list["UserTokenORM"]] = relationship(back_populates="user", lazy="selectin")


from .organization import OrganizationORM
from .user_token import UserTokenORM

