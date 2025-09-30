"""
add_workspace_in_task.

Revision ID: 626b98421d07
Revises: 2b16229b1d95
Create Date: 2025-09-16 00:00:12.463642

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "626b98421d07"
down_revision: Union[str, Sequence[str], None] = "2b16229b1d95"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tasks", sa.Column("workspace_id", sa.Integer(), nullable=False))
    op.alter_column("tasks", "project_id",
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_unique_constraint("uix_workspace_number", "tasks", ["workspace_id", "number"])
    op.create_foreign_key(None, "tasks", "workspaces", ["workspace_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, "tasks", type_="foreignkey")
    op.drop_constraint("uix_workspace_number", "tasks", type_="unique")
    op.alter_column("tasks", "project_id",
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column("tasks", "workspace_id")

