"""
add_projects_colors.

Revision ID: e2415f42e6cf
Revises: 626b98421d07
Create Date: 2025-10-01 00:42:48.105356

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2415f42e6cf"
down_revision: Union[str, Sequence[str], None] = "626b98421d07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("projects", sa.Column("color", sa.String(), nullable=True))
    op.execute("UPDATE projects SET color = '#2DA608'")
    op.alter_column("projects", "color", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("projects", "color")

