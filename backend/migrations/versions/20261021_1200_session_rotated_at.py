"""session rotated_at

Refresh replay detection fired for any revoked session, so a device signed out
by a bulk revoke set off another bulk revoke on its next refresh, and the
devices kept signing each other out. Only a rotated pair counts as a replay now.

Rotation stamped revoked_at and last_used_at with the same instant, which
identifies the sessions rotated before this column existed.

Revision ID: 3b7d0c51a9e4
Revises: f13f869ee726
Create Date: 2026-10-21 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '3b7d0c51a9e4'
down_revision: str | None = 'f13f869ee726'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('sessions', sa.Column('rotated_at', sa.DateTime(timezone=True), nullable=True))
    op.execute('UPDATE sessions SET rotated_at = revoked_at WHERE revoked_at = last_used_at')


def downgrade() -> None:
    op.drop_column('sessions', 'rotated_at')
