"""team report index

Reports now cover a whole workspace over a period, not one user's entries.
The new index starts with workspace_id, so the old one-column index goes.

Revision ID: 842b22fc7f41
Revises: e7991b700037
Create Date: 2026-10-20 02:27:39.289711
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '842b22fc7f41'
down_revision: str | None = 'e7991b700037'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index('ix_time_entries_workspace_id', table_name='time_entries')
    op.create_index('ix_time_entries_workspace_started_at', 'time_entries', ['workspace_id', sa.literal_column('started_at DESC')], unique=False)


def downgrade() -> None:
    op.drop_index('ix_time_entries_workspace_started_at', table_name='time_entries')
    op.create_index('ix_time_entries_workspace_id', 'time_entries', ['workspace_id'], unique=False)
