"""workspace members

Who may work in a workspace and with which role. Every existing workspace gets
its owner as an admin, so nothing changes for current accounts.

Revision ID: 7d1e4a9b2c63
Revises: 5ba8c89254aa
Create Date: 2026-10-20 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '7d1e4a9b2c63'
down_revision: str | None = '5ba8c89254aa'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'workspace_members',
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('workspace_id', 'user_id'),
    )
    op.create_index('ix_workspace_members_user_id', 'workspace_members', ['user_id'], unique=False)
    op.execute(
        """
        INSERT INTO workspace_members (workspace_id, user_id, role, created_at)
        SELECT id, owner_id, 'admin', created_at FROM workspaces
        """
    )


def downgrade() -> None:
    op.drop_index('ix_workspace_members_user_id', table_name='workspace_members')
    op.drop_table('workspace_members')
