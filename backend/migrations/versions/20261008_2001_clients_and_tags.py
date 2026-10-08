"""clients and tags

Clients group projects (`projects.client_id`), tags label time entries through
`time_entry_tags`. Both belong to a workspace. Existing data needs no
backfill: every project starts without a client, every entry without tags.

Revision ID: c21c905afcbf
Revises: c2cffb9d595a
Create Date: 2026-10-08 20:01:27.158021
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'c21c905afcbf'
down_revision: str | None = 'c2cffb9d595a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'clients',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_clients_workspace_id', 'clients', ['workspace_id'], unique=False)
    op.create_index('uq_clients_workspace_active_name', 'clients', ['workspace_id', sa.literal_column('lower(name)')], unique=True, postgresql_where=sa.text('archived_at IS NULL'))

    op.add_column('projects', sa.Column('client_id', sa.UUID(), nullable=True))
    op.create_foreign_key(None, 'projects', 'clients', ['client_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_projects_client_id', 'projects', ['client_id'], unique=False)

    op.create_table(
        'tags',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('uq_tags_workspace_name', 'tags', ['workspace_id', sa.literal_column('lower(name)')], unique=True)

    op.create_table(
        'time_entry_tags',
        sa.Column('time_entry_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['time_entry_id'], ['time_entries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('time_entry_id', 'tag_id'),
    )
    op.create_index('ix_time_entry_tags_tag_id', 'time_entry_tags', ['tag_id'], unique=False)


def downgrade() -> None:
    # Clients and tags have nowhere to go at the previous revision and are dropped.
    op.drop_index('ix_time_entry_tags_tag_id', table_name='time_entry_tags')
    op.drop_table('time_entry_tags')
    op.drop_index('uq_tags_workspace_name', table_name='tags')
    op.drop_table('tags')

    # Dropping the column takes its foreign key with it.
    op.drop_index('ix_projects_client_id', table_name='projects')
    op.drop_column('projects', 'client_id')

    op.drop_index('uq_clients_workspace_active_name', table_name='clients', postgresql_where=sa.text('archived_at IS NULL'))
    op.drop_index('ix_clients_workspace_id', table_name='clients')
    op.drop_table('clients')
