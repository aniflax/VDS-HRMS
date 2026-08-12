"""add_activated_at

Revision ID: a1b2c3d4e5f6
Revises: f3a2b1c4d5e6
Create Date: 2026-04-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f3a2b1c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sevaks',
        sa.Column('activated_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('sevaks', 'activated_at')