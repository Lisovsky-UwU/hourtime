"""tasks

Revision ID: 52a45f4ea9a1
Revises: 3b7d0c51a9e4
Create Date: 2026-11-01 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '52a45f4ea9a1'
down_revision: str | None = '3b7d0c51a9e4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'tasks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('estimated_seconds', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('estimated_seconds > 0', name='ck_tasks_estimated_seconds_positive'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tasks_project_id', 'tasks', ['project_id'], unique=False)
    op.create_index('uq_tasks_project_active_name', 'tasks', ['project_id', sa.literal_column('lower(name)')], unique=True, postgresql_where=sa.text('completed_at IS NULL'))


def downgrade() -> None:
    op.drop_index('uq_tasks_project_active_name', table_name='tasks', postgresql_where=sa.text('completed_at IS NULL'))
    op.drop_index('ix_tasks_project_id', table_name='tasks')
    op.drop_table('tasks')
