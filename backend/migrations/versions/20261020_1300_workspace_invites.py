"""workspace invites

One-time links that let someone join a workspace. Additive only.

Revision ID: e7991b700037
Revises: 7d1e4a9b2c63
Create Date: 2026-10-20 02:07:24.611710
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'e7991b700037'
down_revision: str | None = '7d1e4a9b2c63'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('workspace_invites',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('workspace_id', sa.UUID(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('role', sa.String(length=16), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash')
    )
    op.create_index('ix_workspace_invites_workspace_id', 'workspace_invites', ['workspace_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_workspace_invites_workspace_id', table_name='workspace_invites')
    op.drop_table('workspace_invites')
