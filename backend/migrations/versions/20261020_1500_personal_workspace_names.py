"""personal workspace names

Personal workspaces were all called "Personal", so a member of someone else's
saw two of them in the switcher. They take the owner's email instead; ones the
owner already renamed keep their name.

Revision ID: f13f869ee726
Revises: 842b22fc7f41
Create Date: 2026-10-20 02:33:58.228952
"""

from collections.abc import Sequence

from alembic import op

revision: str = 'f13f869ee726'
down_revision: str | None = '842b22fc7f41'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE workspaces SET name = left(u.email, 100)
        FROM users u WHERE u.id = workspaces.owner_id AND workspaces.name = 'Personal'
        """
    )


def downgrade() -> None:
    # Nothing to undo: the old name carried no information.
    pass
