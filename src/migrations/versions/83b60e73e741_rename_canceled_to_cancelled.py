"""rename canceled to cancelled

Revision ID: 83b60e73e741
Revises: c51e8ec6208a
Create Date: 2026-09-17 17:40:09.957573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83b60e73e741'
down_revision: Union[str, Sequence[str], None] = 'c51e8ec6208a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "tickets",
        "status",
        type_=sa.Enum(
            "active", "cancelled", name="ticketstatus", native_enum=False
        ),
        existing_nullable=False,
        existing_server_default="active",
    )
    op.execute("UPDATE tickets SET status = 'cancelled' WHERE status = 'canceled'")


def downgrade() -> None:
    op.execute("UPDATE tickets SET status = 'canceled' WHERE status = 'cancelled'")
    op.alter_column(
        "tickets",
        "status",
        type_=sa.Enum(
            "active", "canceled", name="ticketstatus", native_enum=False
        ),
        existing_nullable=False,
        existing_server_default="active",
    )
