import uuid
from datetime import datetime

from sqlalchemy import UUID, VARCHAR, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class UserTokenORM(Base):
    __tablename__ = "user_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(VARCHAR(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    user: Mapped["UserORM"] = relationship(back_populates="tokens", lazy="joined")


from .user import UserORM

