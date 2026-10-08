"""billable and rates

Billable flag on entries and projects, hourly rates on projects and a default
rate with a currency on workspaces. Additive only: existing entries and
projects become non-billable, workspaces get no rate and USD.

Revision ID: 5ba8c89254aa
Revises: c21c905afcbf
Create Date: 2026-10-08 21:24:51.347182
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '5ba8c89254aa'
down_revision: str | None = 'c21c905afcbf'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('billable', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('projects', sa.Column('hourly_rate', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('time_entries', sa.Column('billable', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('workspaces', sa.Column('default_hourly_rate', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('workspaces', sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False))


def downgrade() -> None:
    op.drop_column('workspaces', 'currency')
    op.drop_column('workspaces', 'default_hourly_rate')
    op.drop_column('time_entries', 'billable')
    op.drop_column('projects', 'hourly_rate')
    op.drop_column('projects', 'billable')
