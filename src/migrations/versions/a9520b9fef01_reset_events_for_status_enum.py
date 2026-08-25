"""reset events for status enum

Revision ID: a9520b9fef01
Revises: a3b9d278abcb
Create Date: 2026-08-25 11:07:26.818303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9520b9fef01'
down_revision: Union[str, Sequence[str], None] = 'a3b9d278abcb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("TRUNCATE TABLE events")
    op.execute(
        "UPDATE sync_meta SET last_changed_at = '2000-01-01', sync_status = 'never_run'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
