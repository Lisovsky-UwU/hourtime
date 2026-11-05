"""time entry tasks

Revision ID: 436fc2d70503
Revises: 52a45f4ea9a1
Create Date: 2026-11-05 16:39:13.689631
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '436fc2d70503'
down_revision: str | None = '52a45f4ea9a1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('time_entries', sa.Column('task_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_time_entries_task_id_tasks',
        'time_entries',
        'tasks',
        ['task_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_time_entries_task_id', 'time_entries', ['task_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_time_entries_task_id', table_name='time_entries')
    op.drop_constraint('fk_time_entries_task_id_tasks', 'time_entries', type_='foreignkey')
    op.drop_column('time_entries', 'task_id')
