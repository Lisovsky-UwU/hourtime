"""initial schema

Revision ID: 637226572265
Revises: 
Create Date: 2026-09-10 20:51:39.422258
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '637226572265'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('projects',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('color', sa.String(length=7), nullable=False),
    sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_projects_user_id', 'projects', ['user_id'], unique=False)
    op.create_index('uq_projects_user_active_name', 'projects', ['user_id', sa.literal_column('lower(name)')], unique=True, postgresql_where=sa.text('archived_at IS NULL'))
    op.create_table('sessions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('access_token_hash', sa.String(length=64), nullable=False),
    sa.Column('refresh_token_hash', sa.String(length=64), nullable=False),
    sa.Column('access_expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('refresh_expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('user_agent', sa.String(length=512), nullable=True),
    sa.Column('ip', sa.String(length=45), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('access_token_hash'),
    sa.UniqueConstraint('refresh_token_hash')
    )
    op.create_index('ix_sessions_refresh_expires_at', 'sessions', ['refresh_expires_at'], unique=False)
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'], unique=False)
    op.create_table('time_entries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=True),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('stopped_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_time_entries_project_id', 'time_entries', ['project_id'], unique=False)
    op.create_index('ix_time_entries_user_started_at', 'time_entries', ['user_id', sa.literal_column('started_at DESC')], unique=False)
    op.create_index('uq_time_entries_one_running', 'time_entries', ['user_id'], unique=True, postgresql_where=sa.text('stopped_at IS NULL'))


def downgrade() -> None:
    op.drop_index('uq_time_entries_one_running', table_name='time_entries', postgresql_where=sa.text('stopped_at IS NULL'))
    op.drop_index('ix_time_entries_user_started_at', table_name='time_entries')
    op.drop_index('ix_time_entries_project_id', table_name='time_entries')
    op.drop_table('time_entries')
    op.drop_index('ix_sessions_user_id', table_name='sessions')
    op.drop_index('ix_sessions_refresh_expires_at', table_name='sessions')
    op.drop_table('sessions')
    op.drop_index('uq_projects_user_active_name', table_name='projects', postgresql_where=sa.text('archived_at IS NULL'))
    op.drop_index('ix_projects_user_id', table_name='projects')
    op.drop_table('projects')
    op.drop_table('users')
