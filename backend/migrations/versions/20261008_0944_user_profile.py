"""user profile

Revision ID: 300d493fcb79
Revises: 637226572265
Create Date: 2026-10-08 09:44:04.993281
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '300d493fcb79'
down_revision: str | None = '637226572265'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('users', sa.Column('display_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('timezone', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('week_start', sa.SmallInteger(), server_default='1', nullable=False))
    op.add_column('users', sa.Column('duration_format', sa.String(length=16), server_default='classic', nullable=False))
    op.add_column('users', sa.Column('hour_cycle', sa.SmallInteger(), server_default='24', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'hour_cycle')
    op.drop_column('users', 'duration_format')
    op.drop_column('users', 'week_start')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'display_name')
