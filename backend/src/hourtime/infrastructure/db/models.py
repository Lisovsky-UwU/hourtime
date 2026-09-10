"""SQLAlchemy tables.

Deliberately separate from the domain entities: the storage shape may drift
(indexes, denormalisation) without dragging the business rules along.
"""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[UUID]:
    return mapped_column(PgUUID(as_uuid=True), primary_key=True)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = _uuid_pk()
    # Stored already folded to lower case by the domain, so a plain unique
    # index is enough and the citext extension is not needed.
    email: Mapped[str] = mapped_column(sa.String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    access_token_hash: Mapped[str] = mapped_column(sa.String(64), unique=True, nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(sa.String(64), unique=True, nullable=False)
    access_expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    refresh_expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(sa.String(512))
    ip: Mapped[str | None] = mapped_column(sa.String(45))

    __table_args__ = (
        sa.Index("ix_sessions_user_id", "user_id"),
        # Drives the retention sweep.
        sa.Index("ix_sessions_refresh_expires_at", "refresh_expires_at"),
    )


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    color: Mapped[str] = mapped_column(sa.String(7), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)

    __table_args__ = (
        sa.Index("ix_projects_user_id", "user_id"),
        # Names are unique per user among live projects; archived ones may repeat.
        sa.Index(
            "uq_projects_user_active_name",
            "user_id",
            sa.text("lower(name)"),
            unique=True,
            postgresql_where=sa.text("archived_at IS NULL"),
        ),
    )


class TimeEntryModel(Base):
    __tablename__ = "time_entries"

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL")
    )
    description: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    started_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    stopped_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)

    __table_args__ = (
        sa.Index("ix_time_entries_user_started_at", "user_id", sa.text("started_at DESC")),
        sa.Index("ix_time_entries_project_id", "project_id"),
        # One running timer per user. Lifting this constraint is all it takes to
        # allow parallel timers later.
        sa.Index(
            "uq_time_entries_one_running",
            "user_id",
            unique=True,
            postgresql_where=sa.text("stopped_at IS NULL"),
        ),
    )
