"""workspaces

Every user gets a personal workspace, and projects and time entries move into
it. Projects lose `user_id`: from now on they belong to the workspace. Time
entries keep it - it says who tracked the entry.

Revision ID: c2cffb9d595a
Revises: 300d493fcb79
Create Date: 2026-10-08 19:37:49.697707
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'c2cffb9d595a'
down_revision: str | None = '300d493fcb79'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Same name as `PERSONAL_WORKSPACE_NAME`; a migration must not import app code
# that may change after it is written.
PERSONAL_WORKSPACE_NAME = 'Personal'


def upgrade() -> None:
    op.create_table(
        'workspaces',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workspaces_owner_id', 'workspaces', ['owner_id'], unique=False)

    # One workspace per existing user, created when the user was.
    op.add_column('users', sa.Column('default_workspace_id', sa.UUID(), nullable=True))
    op.execute(
        sa.text(
            """
            INSERT INTO workspaces (id, name, owner_id, created_at, updated_at)
            SELECT gen_random_uuid(), :name, id, created_at, created_at FROM users
            """
        ).bindparams(name=PERSONAL_WORKSPACE_NAME)
    )
    op.execute(
        """
        UPDATE users SET default_workspace_id = w.id
        FROM workspaces w WHERE w.owner_id = users.id
        """
    )
    op.alter_column('users', 'default_workspace_id', nullable=False)
    op.create_foreign_key(
        'fk_users_default_workspace_id',
        'users',
        'workspaces',
        ['default_workspace_id'],
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )

    op.add_column('projects', sa.Column('workspace_id', sa.UUID(), nullable=True))
    op.execute(
        """
        UPDATE projects SET workspace_id = u.default_workspace_id
        FROM users u WHERE u.id = projects.user_id
        """
    )
    op.alter_column('projects', 'workspace_id', nullable=False)
    op.create_foreign_key(
        None, 'projects', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE'
    )
    op.drop_index('uq_projects_user_active_name', table_name='projects', postgresql_where=sa.text('archived_at IS NULL'))
    op.drop_index('ix_projects_user_id', table_name='projects')
    op.drop_column('projects', 'user_id')
    op.create_index('ix_projects_workspace_id', 'projects', ['workspace_id'], unique=False)
    op.create_index('uq_projects_workspace_active_name', 'projects', ['workspace_id', sa.literal_column('lower(name)')], unique=True, postgresql_where=sa.text('archived_at IS NULL'))

    op.add_column('time_entries', sa.Column('workspace_id', sa.UUID(), nullable=True))
    op.execute(
        """
        UPDATE time_entries SET workspace_id = u.default_workspace_id
        FROM users u WHERE u.id = time_entries.user_id
        """
    )
    op.alter_column('time_entries', 'workspace_id', nullable=False)
    op.create_foreign_key(
        None, 'time_entries', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE'
    )
    op.create_index('ix_time_entries_workspace_id', 'time_entries', ['workspace_id'], unique=False)


def downgrade() -> None:
    # Only personal workspaces exist at this revision, so the owner of a
    # project's workspace is the user it belonged to before.
    op.drop_index('ix_time_entries_workspace_id', table_name='time_entries')
    op.drop_column('time_entries', 'workspace_id')

    op.add_column('projects', sa.Column('user_id', sa.UUID(), nullable=True))
    op.execute(
        """
        UPDATE projects SET user_id = w.owner_id
        FROM workspaces w WHERE w.id = projects.workspace_id
        """
    )
    op.alter_column('projects', 'user_id', nullable=False)
    op.create_foreign_key(None, 'projects', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.drop_index('uq_projects_workspace_active_name', table_name='projects', postgresql_where=sa.text('archived_at IS NULL'))
    op.drop_index('ix_projects_workspace_id', table_name='projects')
    op.drop_column('projects', 'workspace_id')
    op.create_index('ix_projects_user_id', 'projects', ['user_id'], unique=False)
    op.create_index('uq_projects_user_active_name', 'projects', ['user_id', sa.literal_column('lower(name)')], unique=True, postgresql_where=sa.text('archived_at IS NULL'))

    op.drop_constraint('fk_users_default_workspace_id', 'users', type_='foreignkey')
    op.drop_column('users', 'default_workspace_id')
    op.drop_index('ix_workspaces_owner_id', table_name='workspaces')
    op.drop_table('workspaces')
